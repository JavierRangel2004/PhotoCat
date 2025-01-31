# PhotoCat

![PhotoCat Logo](https://github.com/JavierRangel2004/PhotoCat/blob/main/images/logo.png)

PhotoCat is an advanced photo categorization tool that leverages state-of-the-art machine learning and computer vision techniques to analyze, categorize, and enhance your image library. Whether you're a professional photographer, a digital archivist, or simply someone looking to organize personal photos, PhotoCat provides automated solutions to streamline your workflow.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Image Loading & Preprocessing:** Supports various image formats, including RAW files, with noise reduction and normalization.
- **Blurriness Detection:** Identifies and flags blurry images to maintain a high-quality photo library.
- **Exposure Analysis:** Determines if an image is underexposed, overexposed, or correctly exposed.
- **Object Detection:** Utilizes YOLOv8 for real-time object detection within images.
- **Image Captioning:** Generates descriptive captions using the BLIP model.
- **Color Analysis:** Extracts dominant colors and detects the mood based on color tones.
- **Optical Character Recognition (OCR):** Detects and processes text within images to identify brands or other relevant information.
- **Metadata Writing:** Automatically writes categorized metadata into XMP sidecar files for seamless integration with photo management software.
- **Parallel Processing:** Leverages multiprocessing to efficiently handle large batches of images.

## Installation

### Prerequisites

- **Python 3.8 or higher**
- **Git**

### Clone the Repository

```bash
git clone https://github.com/JavierRangel2004/PhotoCat.git
cd PhotoCat
```

### Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

Ensure you have `pip` updated:

```bash
pip install --upgrade pip
```

Install the required packages:

```bash
pip install -r requirements.txt
```

**Note:** If you encounter SSL certificate issues while downloading NLTK data, refer to the [Troubleshooting NLTK Downloads](#troubleshooting-nltk-downloads) section below.

### Download YOLOv8 Model

Download the YOLOv8 large model and place it in the root directory:

```bash
wget https://path-to-your-model/yolov8l.pt -P .
```

*(Replace the URL with the actual path to the YOLOv8 model if different.)*

## Usage

### Preparing Your Images

Place all the images you want to process in the `images/` directory. Supported formats include `.cr2`, `.cr3`, `.jpg`, `.jpeg`, `.png`, and `.tiff`.

### Running the Categorizer

Execute the main script to start processing your images:

```bash
python src/main.py
```

The script will:

1. **Load Images:** Read images from the `images/` directory.
2. **Analyze Images:** Perform blurriness detection, exposure analysis, object detection, color analysis, OCR, and image captioning.
3. **Generate Metadata:** Assign ratings, tags, and titles based on the analysis.
4. **Write XMP Sidecar Files:** Create or update `.xmp` files with the generated metadata.

### Output

After processing, each image will have an accompanying `.xmp` file containing the metadata. The console will display the processing status, including ratings, tags, and titles for each image.

## Configuration

Configuration flags are defined in `src/main.py` and can be adjusted to enable or disable specific features:

```python
#####################
# Configuration Flags
#####################
ENABLE_BLUR_CHECK = True
ENABLE_EXPOSURE_CHECK = True
ENABLE_OBJECT_DETECTION = True
ENABLE_RATING_LOGIC = True
ENABLE_XMP_WRITING = True
```

Modify these flags as needed to tailor the processing pipeline to your requirements.

## Project Structure

```
PhotoCat/
├── .gitignore
├── README.md
├── requirements.txt
├── images/
│   ├── IMG_1424.CR2
│   └── IMG_1424.xmp
├── src/
│   ├── main.py
│   ├── image_analysis.py
│   ├── image_captioning.py
│   ├── object_detection.py
│   ├── metadata_writer.py
│   └── utilities.py
```

- **.gitignore:** Specifies files and directories to be ignored by Git.
- **requirements.txt:** Lists all Python dependencies required for the project.
- **images/:** Directory containing images to be processed and their corresponding XMP sidecar files.
- **src/:** Contains all source code modules.
  - **main.py:** Entry point for the application.
  - **image_analysis.py:** Functions for image loading, preprocessing, blurriness detection, exposure analysis, and color tone analysis.
  - **image_captioning.py:** Implements image captioning using the BLIP model.
  - **object_detection.py:** Utilizes YOLOv8 for object detection.
  - **metadata_writer.py:** Writes metadata into XMP sidecar files.
  - **utilities.py:** Helper functions for processing images, generating tags, and refining titles.

## Troubleshooting NLTK Downloads

If you encounter SSL certificate verification errors while downloading NLTK data, follow these steps:

### 1. Update SSL Certificates

#### macOS

Run the following command in your terminal:

```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

*(Replace `3.x` with your Python version.)*

#### Windows

Reinstall Python and ensure that the option to install certificates is selected during installation.

#### Linux (Debian/Ubuntu)

```bash
sudo apt-get update
sudo apt-get install --reinstall ca-certificates
```

### 2. Download NLTK Data Manually

1. Visit the [NLTK Data](https://www.nltk.org/data.html) page.
2. Download the required packages (`stopwords`, `punkt`, `wordnet`).
3. Extract the downloaded `.zip` files into the NLTK data directory. You can find the directory by running:

    ```python
    import nltk
    print(nltk.data.path)
    ```

### 3. Disable SSL Verification Temporarily

**Warning:** This method is not recommended for production environments as it compromises security.

```python
import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
```

## Contributing

Contributions are welcome! If you encounter issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

### Steps to Contribute

1. **Fork the Repository**
2. **Create a New Branch**

    ```bash
    git checkout -b feature/YourFeature
    ```

3. **Make Your Changes**
4. **Commit Your Changes**

    ```bash
    git commit -m "Add your message here"
    ```

5. **Push to the Branch**

    ```bash
    git push origin feature/YourFeature
    ```

6. **Open a Pull Request**

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any inquiries or support, please contact:

- **Email:** [inspec_jrm@gmail.com](mailto:inspec_jrm@gmail.com)

Feel free to reach out with questions, feedback, or collaboration ideas!

---

*Happy Categorizing! 📸*