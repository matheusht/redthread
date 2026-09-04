# RedThread image notes

The README uses `readme-logo.png` beside the project name.
The PNG file has a transparent background.
GitHub sets the text color for the page theme.

The built-in imagegen tool made this image from the previous project header.
The image is a project symbol. It does not show a test result.
The final PNG is 256 pixels wide and 256 pixels high.
The resize operation kept the alpha channel.

## Image prompt

Use case: background-extraction
Edit target: the supplied RedThread header.
Extract only the red symbol at the left. Remove the white background and all wordmark text. Preserve the red symbol's exact shape, rounded ends, proportions, and color. Use a tight square canvas with a small clear margin.
Use a real transparent background with an alpha channel. The open center of the symbol must also be transparent. Do not draw a background, checkerboard, border, shadow, or new detail. Keep the red symbol opaque. This image will appear beside normal title text on a GitHub README.
