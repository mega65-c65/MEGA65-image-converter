Image Conversion and Processing Script for MEGA65 Compatibility with Fixed 320x200 Ratio and BASIC Loader Generation

This script is designed to convert an input JPG image into a format compatible with the MEGA65 computer and generate a BASIC loader program. 
It follows these steps:
1. **Image Resizing and Conversion**:
   - The input image is resized to fit exactly within the 320x200 pixels boundary while maintaining the aspect ratio.
   - The script uses ImageMagick to handle resizing, with any unfilled areas set to black.
   - The resized image is converted directly to a PPM file with a maximum of 128 colors and a density of 72 PPI.

2. **Initial IFF Conversion**:
   - The PPM image is converted to IFF format using `ppmtoilbm`.
   - The script captures the output from `ppmtoilbm` to check the number of colors in the image.

3. **Color Count Analysis**:
   - If the image contains fewer than 128 colors, it is left as-is.
   - If 128 colors or more are detected, the script reduces the color depth to 4 bits per channel (MEGA65 compatibility) and reconverts it to IFF.

4. **D81 Disk Image Creation**:
   - The script creates a D81 disk image using `cc1541` and adds the generated IFF file to it.

5. **BASIC Loader Program Generation**:
   - A BASIC65 loader program is created that loads the IFF image.
   - The script generates a `.bas` file and converts it to a `.prg` file using the `petcat` utility.
   - The loader program is then added to the D81 disk image.

After processing, the script prompts the user if they want to run the conversion again.

Requirements:
- ImageMagick (`convert` command)
- NetPBM tools (`ppmtoilbm`, `ppmquant`)
- `cc1541` for creating the D81 disk image
- `petcat` for converting the BASIC loader to a PRG file

To run the script, type "python3 IC65_128_3.py" in the Linux console.

Author: [RaulSQ]
Date: [30.09.2024]
