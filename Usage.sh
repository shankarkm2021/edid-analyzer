# Analyze from file
python src/edid_parser.py --file samples/tv.bin --report

# Analyze from hex string
python src/edid_parser.py --hex "00ffffffffffff004d2d010101010101" --report

# Read directly from device (requires root)
sudo python src/edid_parser.py --device /dev/i2c-0 --report
