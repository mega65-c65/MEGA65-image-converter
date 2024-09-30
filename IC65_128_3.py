"""
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
"""

import subprocess
import os
import struct

def run_conversion():
    # Prompt the user for the input JPG file name
    input_image = input("Enter the input image file name (e.g., mega65.jpg): ").strip()

    # Derive the PPM and IFF file names based on the input JPG file name
    base_name = os.path.splitext(input_image)[0]  # Removes the extension
    output_ppm = f"{base_name}.ppm"
    output_iff = f"{base_name}.iff"

    # Set fixed values
    colors = "128"
    depth = "7"
    density = "72"  # Always set to 72

    # Step 1: Use ImageMagick to resize and convert the image to PPM in a single step
    convert_command = [
        "convert",
	"-units", "PixelsPerInch",
        input_image,
        "-resize", "320x200",       # Resize the image within 320x200 while maintaining aspect ratio
        "-background", "black",     # Set the background color to black
        "-gravity", "center",       # Center the image on the canvas
        "-extent", "320x200",       # Ensure the final image size is exactly 320x200 pixels
        "+dither",
        "-colors", colors,
        "-depth", depth,
        "-density", density,
        output_ppm                  # Output directly to PPM
    ]

    try:
        print("Running ImageMagick conversion and resizing...")
        subprocess.run(convert_command, check=True)
        print(f"Conversion to PPM completed. Output file: {output_ppm}")
    except subprocess.CalledProcessError as e:
        print(f"Error during ImageMagick conversion: {e}")
        return

    # Check if the PPM output file exists
    if not os.path.exists(output_ppm):
        print(f"Error: PPM file '{output_ppm}' was not created. Exiting.")
        return

    # Step 2: Convert PPM to IFF using ppmtoilbm
    ppmtoilbm_command = f"ppmtoilbm -aga -normal -fixplanes 7 {output_ppm} > {output_iff}"

    try:
        print("Converting PPM to IFF format using ppmtoilbm...")
        result = subprocess.run(ppmtoilbm_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Conversion to IFF completed successfully. Output file: {output_iff}")

            # Analyze the ppmtoilbm output for color count
            if "colors found" in result.stderr:
                color_count = int(result.stderr.split("colors found")[0].split()[-1])
                print(f"ppmtoilbm detected {color_count} colors.")

                # If more than or equal to 128 colors, proceed with the 4-bit color reduction
                if color_count >= 128:
                    print(f"{color_count} colors detected. Proceeding with MEGA65 4-bit color reduction.")
                    
                    # Step 3: Apply the 4-bit reduction
                    from PIL import Image
                    with Image.open(output_ppm) as img:
                        def reduce_to_4bit_color(img):
                            # Convert each color channel to the nearest 4-bit value (0-15)
                            def to_4bit(value):
                                return int((value / 255) * 15) * 17  # Scales 0-15 back to 0-255 (e.g., 15 -> 255, 1 -> 17)

                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            pixels = img.load()
                            for y in range(img.height):
                                for x in range(img.width):
                                    r, g, b = pixels[x, y]
                                    pixels[x, y] = (to_4bit(r), to_4bit(g), to_4bit(b))
                            
                            return img

                        img = reduce_to_4bit_color(img)
                        img.save(output_ppm, 'PPM')
                        print("Color values reduced to 4 bits per channel (MEGA65 compatibility).")

                        # Repeat conversion to IFF after reduction
                        ppmtoilbm_command = f"ppmtoilbm -aga -normal -fixplanes 7 {output_ppm} > {output_iff}"
                        subprocess.run(ppmtoilbm_command, shell=True, check=True)
                        print(f"Final conversion to IFF completed with 4-bit colors. Output file: {output_iff}")
                else:
                    print("Image has fewer than 128 colors. No further reduction needed.")
        else:
            print(f"Error during PPM to IFF conversion: {result.stderr}")
            return

    except subprocess.CalledProcessError as e:
        print(f"Error during PPM to IFF conversion: {e}")
        print(f"ppmtoilbm output: {e.stderr}")  # Display the detailed error output
        return

    # Check if the IFF output file exists
    if not os.path.exists(output_iff):
        print(f"Error: IFF file '{output_iff}' was not created.")
        return

    # Step 3: Create a D81 disk image using cc1541
    disk_name = input("Enter the name for the D81 disk (e.g., mega65club): ").strip()
    output_d81 = f"{disk_name}.d81"  # The D81 file name will be based on the disk name input

    # Extract the local filename for the IFF file
    local_filename = os.path.basename(output_iff)

    cc1541_command = [
        "cc1541",
        "-n", disk_name,           # Set the disk name
        "-f", local_filename,      # Use the local filename for the file to add
        "-w", output_iff,          # Specify the actual IFF file to write to the disk image
        output_d81                 # Output disk image file
    ]

    try:
        print(f"Creating D81 disk image with the name '{disk_name}' and adding '{local_filename}'...")
        subprocess.run(cc1541_command, check=True)
        print(f"D81 disk image '{output_d81}' created successfully with '{local_filename}' added to it.")
    except subprocess.CalledProcessError as e:
        print(f"Error during D81 disk creation: {e}")
        return

    # Check if the D81 output file exists
    if os.path.exists(output_d81):
        print(f"D81 disk image '{output_d81}' created successfully.")
    else:
        print("Error: D81 disk image was not created.")

    # Step 4: Create a BASIC loader BAS file and convert to PRG using petcat
    try:
        print("Generating the BASIC loader BAS file...")
        loader_bas = f"{base_name}.bas"
        loader_prg = f"{base_name}.prg"
        
        with open(loader_bas, 'w') as bas_file:
            # Define the BASIC lines
            bas_file.write("10 screen 320,200,7\n")
            bas_file.write(f'20 loadiff "{local_filename}",u9: rem considering {disk_name}.d81 is mounted on unit 9\n')
            bas_file.write("30 getkey a$\n")
            bas_file.write("40 screen close\n")

        print(f"Loader BAS file '{loader_bas}' created successfully.")

        # Convert the BAS file to a PRG file using petcat
        petcat_command = ["petcat", "-w65", "-o", loader_prg, "--", loader_bas]
        subprocess.run(petcat_command, check=True)
        print(f"Loader PRG file '{loader_prg}' created successfully using petcat.")

        # Add the loader PRG to the D81 disk image using cc1541
        cc1541_add_prg_command = [
            "cc1541",
            "-n", disk_name,
            "-f", base_name,
            "-w", loader_prg,
            output_d81
        ]

        subprocess.run(cc1541_add_prg_command, check=True)
        print(f"Loader PRG '{loader_prg}' added to D81 disk image '{output_d81}' successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error adding loader PRG to D81 disk image: {e}")
    except Exception as ex:
        print(f"Error creating the BASIC loader PRG file: {ex}")

# Main loop to allow running the script multiple times
while True:
    run_conversion()
    retry = input("Do you want to run the script again? (Y/N): ").strip().lower()
    if retry != 'y':
        print("Exiting the script. Goodbye!")
        break

