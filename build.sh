#!/bin/bash

# Build script for optimizing website performance

# Configuration
SOURCE_DIR="/Users/bytedance/resume"
BUILD_DIR="$SOURCE_DIR/build"
HTML_FILES=$(find $SOURCE_DIR -name "*.html" -type f)

# Create build directory if it doesn't exist
mkdir -p $BUILD_DIR

# Function to minify HTML
minify_html() {
    local input_file=$1
    local output_file=$2

    # Minify HTML using regex substitutions
    sed 's/^[ \t]*//' "$input_file" |  # Remove leading whitespace
    tr -d '\n\r' |  # Remove newlines
    sed 's/\s\+/ /g' |  # Replace multiple spaces with single space
    sed 's/\s*</</g' |  # Remove space before tags
    sed 's/>\s*/>/g' |  # Remove space after tags
    sed 's/\s*=\s*/=/g' |  # Remove spaces around equals signs
    sed 's/<!--.*-->//g' > "$output_file"  # Remove comments

    echo "Minified: $input_file -> $output_file"
}

# Function to copy and optimize images
optimize_images() {
    # Copy all images
    cp -r "$SOURCE_DIR/img" "$BUILD_DIR/" 2>/dev/null || true
    cp -r "$SOURCE_DIR/attaches" "$BUILD_DIR/" 2>/dev/null || true

    # Optimize images if tools are available
    if command -v pngquant &> /dev/null; then
        find "$BUILD_DIR/img" -name "*.png" -exec pngquant --quality=65-80 --ext=.png --force {} \;
    fi

    if command -v jpegoptim &> /dev/null; then
        find "$BUILD_DIR/img" -name "*.jpg" -name "*.jpeg" -exec jpegoptim --max=70 --strip-all {} \;
    fi

    echo "Images optimized"
}

# Main build process
echo "Starting build process..."

# Copy CSS files
mkdir -p "$BUILD_DIR/css"
cp "$SOURCE_DIR/css/index.min.css" "$BUILD_DIR/css/" 2>/dev/null || true

# Copy JS files
mkdir -p "$BUILD_DIR/js"
cp "$SOURCE_DIR/js/main.min.js" "$BUILD_DIR/js/" 2>/dev/null || true

# Copy other static assets
cp -r "$SOURCE_DIR/fonts" "$BUILD_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/more" "$BUILD_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/friends" "$BUILD_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/2021" "$BUILD_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/archives" "$BUILD_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/2025" "$BUILD_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/zh-cn" "$BUILD_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/vendor" "$BUILD_DIR/" 2>/dev/null || true

# Minify all HTML files
for html_file in $HTML_FILES; do
    # Calculate relative path
    relative_path=${html_file#$SOURCE_DIR/}
    output_file="$BUILD_DIR/$relative_path"

    # Create directory if needed
    mkdir -p "$(dirname "$output_file")"

    # Minify HTML
    minify_html "$html_file" "$output_file"
done

# Optimize images
optimize_images

echo "Build completed successfully!"
echo "Build directory: $BUILD_DIR"

# Provide instructions
echo -e "\nDeployment options:"
echo "1. Serve locally: python3 -m http.server 8000 --directory $BUILD_DIR"
echo "2. Upload to hosting: rsync -avz $BUILD_DIR/ user@server:/path/to/web/root"
echo "3. Deploy to GitHub Pages: gh-pages -d $BUILD_DIR"