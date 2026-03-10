#!/usr/bin/env python3
"""
EDID Parser - Extract and analyze EDID data from HDMI connections
Compatible with CEA-861 and VESA EDID standards
"""

import struct
import binascii
from typing import Dict, List, Optional, Tuple

class EDIDParser:
    """Parse Extended Display Identification Data from HDMI devices"""
    
    # EDID header - should be 00 FF FF FF FF FF FF 00
    EXPECTED_HEADER = b'\x00\xff\xff\xff\xff\xff\xff\x00'
    
    # Standard timings codes
    STANDARD_TIMINGS = {
        0x01: "640x480 @ 60Hz",
        0x02: "800x600 @ 60Hz",
        0x03: "1024x768 @ 60Hz",
        0x04: "1280x1024 @ 60Hz",
        0x05: "1400x1050 @ 60Hz",
        # Add more as needed
    }
    
    def __init__(self, edid_data: bytes):
        """
        Initialize parser with raw EDID data
        
        Args:
            edid_data: Raw EDID bytes (typically 128 or 256 bytes)
        """
        self.raw_data = edid_data
        self.parsed = {}
        self.errors = []
        
    def validate_header(self) -> bool:
        """Validate EDID header"""
        if len(self.raw_data) < 8:
            self.errors.append("EDID data too short")
            return False
            
        header = self.raw_data[:8]
        if header != self.EXPECTED_HEADER:
            self.errors.append(f"Invalid EDID header: {binascii.hexlify(header)}")
            return False
        return True
    
    def parse_basic_info(self) -> Dict:
        """Parse manufacturer and product information"""
        if len(self.raw_data) < 18:
            return {}
            
        # Manufacturer ID (3 letters, 5 bits each)
        manuf_bytes = struct.unpack('>H', self.raw_data[8:10])[0]
        manuf = self._decode_manufacturer(manuf_bytes)
        
        # Product ID
        product_id = struct.unpack('<H', self.raw_data[10:12])[0]
        
        # Serial number
        serial = struct.unpack('<I', self.raw_data[12:16])[0]
        
        # Manufacture week/year
        week = self.raw_data[16]
        year = self.raw_data[17] + 1990
        
        return {
            'manufacturer': manuf,
            'product_id': hex(product_id),
            'serial_number': hex(serial) if serial != 0 else "Not specified",
            'manufacture_date': f"Week {week}, {year}" if week != 0 else f"Year {year}"
        }
    
    def _decode_manufacturer(self, code: int) -> str:
        """Decode 16-bit manufacturer code to 3 letters"""
        letters = []
        for i in range(2, -1, -1):
            char_code = (code >> (5 * i)) & 0x1F
            if 1 <= char_code <= 26:
                letters.append(chr(ord('A') + char_code - 1))
            else:
                letters.append('?')
        return ''.join(letters)
    
    def parse_edid_version(self) -> Dict:
        """Parse EDID version information"""
        if len(self.raw_data) < 20:
            return {}
            
        version = self.raw_data[18]
        revision = self.raw_data[19]
        
        return {
            'version': f"{version}.{revision}",
            'major': version,
            'minor': revision
        }
    
    def parse_display_params(self) -> Dict:
        """Parse basic display parameters"""
        if len(self.raw_data) < 25:
            return {}
            
        # Video input definition byte
        video_byte = self.raw_data[20]
        
        # Max horizontal/vertical size (cm)
        max_h_size = self.raw_data[21]
        max_v_size = self.raw_data[22]
        
        # Gamma (divide by 100, add 1)
        gamma = (self.raw_data[23] / 100) + 1 if self.raw_data[23] != 0xFF else "Unknown"
        
        # Features byte
        features = self.raw_data[24]
        
        # Parse video input type
        if video_byte & 0x80:
            input_type = "Digital"
            # Digital interface: bits 6-4 indicate interface
            interface_code = (video_byte >> 4) & 0x07
            interfaces = ["Undefined", "DVI", "HDMI-a", "HDMI-b", "MDDI", "DisplayPort"]
            interface = interfaces[interface_code] if interface_code < len(interfaces) else "Unknown"
        else:
            input_type = "Analog"
            interface = "Analog"
        
        return {
            'video_input': {
                'type': input_type,
                'interface': interface
            },
            'screen_size': {
                'width_cm': max_h_size if max_h_size != 0 else "Unknown",
                'height_cm': max_v_size if max_v_size != 0 else "Unknown"
            },
            'gamma': gamma,
            'features': {
                'dpms_standby': bool(features & 0x01),
                'dpms_suspend': bool(features & 0x02),
                'dpms_active_off': bool(features & 0x04),
                'display_type': ['Monochrome', 'RGB', 'Non-RGB Multicolor'][(features >> 3) & 0x03],
                'standard_srgb': bool(features & 0x40),
                'preferred_timing': bool(features & 0x80)
            }
        }
    
    def parse_color_characteristics(self) -> Dict:
        """Parse color characteristics (CIE xy coordinates)"""
        if len(self.raw_data) < 35:
            return {}
            
        # Red, Green, Blue, White point coordinates (10 bits each)
        color_bytes = self.raw_data[25:35]
        
        # Parse coordinates (simplified)
        # Full implementation would extract 10-bit values
        
        return {
            'color_encoding': "RGB 4:4:4",  # Simplified
            'color_depth': "8-bit per channel"  # Default assumption
        }
    
    def parse_established_timings(self) -> List[str]:
        """Parse established timings (bytes 35-37)"""
        if len(self.raw_data) < 38:
            return []
            
        timings = []
        timing_bytes = self.raw_data[35:38]
        
        # Standard VESA timings
        timing_map = {
            (35, 0x80): "720x400 @ 70Hz",
            (35, 0x40): "720x400 @ 88Hz",
            (35, 0x20): "640x480 @ 60Hz",
            (35, 0x10): "640x480 @ 67Hz",
            (35, 0x08): "640x480 @ 72Hz",
            (35, 0x04): "640x480 @ 75Hz",
            (35, 0x02): "800x600 @ 56Hz",
            (35, 0x01): "800x600 @ 60Hz",
            (36, 0x80): "800x600 @ 72Hz",
            (36, 0x40): "800x600 @ 75Hz",
            (36, 0x20): "832x624 @ 75Hz",
            (36, 0x10): "1024x768 @ 87Hz (interlaced)",
            (36, 0x08): "1024x768 @ 60Hz",
            (36, 0x04): "1024x768 @ 70Hz",
            (36, 0x02): "1024x768 @ 75Hz",
            (36, 0x01): "1280x1024 @ 75Hz",
            (37, 0x80): "1152x870 @ 75Hz",
        }
        
        for byte_idx, mask, timing in [(35, 0x80, "720x400 @ 70Hz"), (35, 0x40, "720x400 @ 88Hz")]:
            if timing_bytes[byte_idx - 35] & mask:
                timings.append(timing)
        
        return timings
    
    def parse_hdmi_vsdb(self, block: bytes) -> Dict:
        """Parse HDMI Vendor Specific Data Block"""
        if len(block) < 5:
            return {}
            
        hdmi_info = {
            'present': True,
            'ieee_id': f"0x{block[1:4].hex()}",
            'version': block[4] & 0x0F,
            'max_tmds_clock': block[4] >> 4,
        }
        
        # Parse capabilities
        if len(block) > 5:
            capabilities = block[5]
            hdmi_info['3d_present'] = bool(capabilities & 0x80)
            hdmi_info['dual_view'] = bool(capabilities & 0x40)
            hdmi_info['deep_color'] = {
                '30bit': bool(capabilities & 0x08),
                '36bit': bool(capabilities & 0x04),
                '48bit': bool(capabilities & 0x02)
            }
            
        return hdmi_info
    
    def parse_cea_extensions(self) -> List[Dict]:
        """Parse CEA-861 extension blocks"""
        extensions = []
        
        if len(self.raw_data) < 128:
            return extensions
            
        # Check for CEA extension (block 1)
        if self.raw_data[126] == 0x02:  # CEA extension tag
            cea_data = self.raw_data[128:256] if len(self.raw_data) > 128 else self.raw_data[128:]
            
            extension = {
                'type': 'CEA-861',
                'revision': self.raw_data[127],
                'data_blocks': []
            }
            
            # Parse data blocks
            offset = 4  # Skip header
            while offset < len(cea_data) and cea_data[offset] != 0:
                block_tag = (cea_data[offset] >> 5) & 0x07
                block_len = cea_data[offset] & 0x1F
                
                if block_tag == 0x03:  # Vendor specific
                    vsdb = cea_data[offset+1:offset+1+block_len]
                    if block_len >= 5 and vsdb[:3] == b'\x03\x0c\x00':  # HDMI identifier
                        extension['hdmi'] = self.parse_hdmi_vsdb(vsdb)
                
                offset += 1 + block_len
            
            extensions.append(extension)
            
        return extensions
    
    def validate_checksum(self) -> bool:
        """Validate EDID checksum"""
        if len(self.raw_data) < 128:
            return False
            
        checksum = sum(self.raw_data[:128]) & 0xFF
        return checksum == 0
    
    def parse_all(self) -> Dict:
        """Parse all EDID information"""
        if not self.validate_header():
            return {'error': 'Invalid EDID header', 'errors': self.errors}
        
        result = {
            'valid': self.validate_checksum(),
            'basic_info': self.parse_basic_info(),
            'version': self.parse_edid_version(),
            'display_params': self.parse_display_params(),
            'color_info': self.parse_color_characteristics(),
            'established_timings': self.parse_established_timings(),
            'extensions': self.parse_cea_extensions(),
            'raw_hex': binascii.hexlify(self.raw_data[:128]).decode('ascii')
        }
        
        return result
    
    def generate_report(self) -> str:
        """Generate human-readable report"""
        data = self.parse_all()
        
        report = []
        report.append("=" * 60)
        report.append("EDID ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        if 'error' in data:
            report.append(f"ERROR: {data['error']}")
            for err in data.get('errors', []):
                report.append(f"  - {err}")
            return "\n".join(report)
        
        # Basic info
        report.append("MANUFACTURER INFORMATION")
        report.append("-" * 40)
        basic = data['basic_info']
        report.append(f"Manufacturer: {basic.get('manufacturer', 'Unknown')}")
        report.append(f"Product ID: {basic.get('product_id', 'Unknown')}")
        report.append(f"Serial Number: {basic.get('serial_number', 'Unknown')}")
        report.append(f"Manufacture Date: {basic.get('manufacture_date', 'Unknown')}")
        report.append("")
        
        # Version
        report.append("EDID VERSION")
        report.append("-" * 40)
        report.append(f"Version: {data['version'].get('version', 'Unknown')}")
        report.append("")
        
        # Display parameters
        report.append("DISPLAY CHARACTERISTICS")
        report.append("-" * 40)
        disp = data['display_params']
        report.append(f"Video Input: {disp['video_input']['type']} ({disp['video_input']['interface']})")
        report.append(f"Screen Size: {disp['screen_size']['width_cm']}cm x {disp['screen_size']['height_cm']}cm")
        report.append(f"Gamma: {disp['gamma']}")
        report.append("Features:")
        for feat, val in disp['features'].items():
            report.append(f"  - {feat}: {val}")
        report.append("")
        
        # Supported timings
        report.append("SUPPORTED TIMINGS")
        report.append("-" * 40)
        for timing in data['established_timings']:
            report.append(f"  ✓ {timing}")
        if not data['established_timings']:
            report.append("  No standard timings found")
        report.append("")
        
        # HDMI capabilities
        for ext in data.get('extensions', []):
            if 'hdmi' in ext:
                report.append("HDMI CAPABILITIES")
                report.append("-" * 40)
                hdmi = ext['hdmi']
                report.append(f"HDMI Present: Yes")
                report.append(f"Version: {hdmi.get('version', 'Unknown')}")
                report.append(f"Max TMDS Clock: {hdmi.get('max_tmds_clock', 0) * 25}MHz")
                if 'deep_color' in hdmi:
                    report.append("Deep Color Support:")
                    for depth, supported in hdmi['deep_color'].items():
                        if supported:
                            report.append(f"  - {depth}")
        report.append("")
        
        # Checksum
        report.append("VALIDATION")
        report.append("-" * 40)
        report.append(f"Checksum: {'✓ Valid' if data['valid'] else '✗ Invalid'}")
        report.append("")
        
        return "\n".join(report)


def read_edid_from_device(device_path: str = "/dev/i2c-0") -> Optional[bytes]:
    """
    Read EDID from I2C device (DDC channel)
    
    Args:
        device_path: Path to I2C device (typically /dev/i2c-N)
    
    Returns:
        EDID bytes or None if reading fails
    """
    try:
        import fcntl
        import ioctl  # May need to install python-ioctl
        
        # DDC I2C address for EDID
        DDC_ADDR = 0x50
        
        # Open I2C device
        fd = open(device_path, 'rb+', 0)
        
        # Set slave address
        fcntl.ioctl(fd, 0x0703, DDC_ADDR)  # I2C_SLAVE
        
        # Read EDID (128 bytes)
        edid_data = bytearray(128)
        
        # Write segment pointer (if needed for >256 byte EDID)
        fd.write(b'\x00')
        
        # Read data
        for i in range(128):
            edid_data[i] = ord(fd.read(1))
        
        fd.close()
        return bytes(edid_data)
        
    except Exception as e:
        print(f"Error reading EDID: {e}")
        return None


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="HDMI EDID Analyzer")
    parser.add_argument("--file", "-f", help="Read EDID from binary file")
    parser.add_argument("--hex", "-x", help="Read EDID from hex string")
    parser.add_argument("--device", "-d", help="Read EDID from I2C device (e.g., /dev/i2c-0)")
    parser.add_argument("--report", "-r", action="store_true", help="Generate detailed report")
    
    args = parser.parse_args()
    
    edid_data = None
    
    if args.file:
        with open(args.file, 'rb') as f:
            edid_data = f.read()
    elif args.hex:
        edid_data = binascii.unhexlify(args.hex.replace(' ', '').replace('\n', ''))
    elif args.device:
        edid_data = read_edid_from_device(args.device)
    else:
        # Use sample EDID for testing
        # This is a minimal valid EDID
        sample = (b'\x00\xff\xff\xff\xff\xff\xff\x00' +  # Header
                 b'\x4d\x2d\x01\x01\x01\x01\x01\x01' +  # Manufacturer
                 b'\x01\x14' +                           # Version
                 b'\x01\x02' +                           # Revision
                 b'\x80\x40\x00\x00' +                   # Basic params
                 b'\x00\x00\x00\x00\x00\x00' +           # Color info
                 b'\x00\x00\x00\x00\x00\x00' +           # Timings
                 b'\x00\x00\x00\x00\x00\x00' +           # Descriptors
                 b'\x00\x00\x00\x00\x00\x00' +           # Descriptors
                 b'\x00\x00\x00\x00\x00\x00' +           # Descriptors
                 b'\x00\x00\x00\x00\x00\x00' +           # Descriptors
                 b'\x00\x00\x00\x00\x00\x00' +           # Extension
                 b'\x00\xf1')                             # Checksum
        edid_data = sample
    
    parser = EDIDParser(edid_data)
    
    if args.report:
        print(parser.generate_report())
    else:
        import json
        print(json.dumps(parser.parse_all(), indent=2, default=str))