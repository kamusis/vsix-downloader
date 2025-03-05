### How to Download a VSIX File from the VS Code Marketplace

If an extension's repository does not provide a VSIX file, you can manually download it from the Visual Studio Code Marketplace. Follow these steps:

1. Visit the [Visual Studio Code Marketplace](https://marketplace.visualstudio.com/vscode).

2. Search for the desired extension (e.g., Deno).

   ![Search Example](https://p16-arcosite-va.ibyteimg.com/obj/tos-maliva-i-10qhjjqwgv-us/9f85346b36e24b24a7980dbd888ba815)

3. Select your desired extension from the search results to view its details page.

4. On the extension's details page, click **Version History**.

5. Extract the following values from the URL and version history information. For example, given the URL:

   `https://marketplace.visualstudio.com/items?itemName=denoland.vscode-deno`

   Extract:
   - **itemName**: The value after `itemName=` (e.g., `denoland.vscode-deno`). Split this into:
     - **fieldA**: The part before the dot (e.g., `denoland`)
     - **fieldB**: The part after the dot (e.g., `vscode-deno`)
   - **version**: The latest version number from the Version History page (e.g., `3.43.3`)

   ![Version History Example](https://p16-arcosite-va.ibyteimg.com/obj/tos-maliva-i-10qhjjqwgv-us/8f83dba24ddb4fdda6077ae1de035488)

6. Use the extracted values to construct the download URL using this template:

   ```bash
   https://marketplace.visualstudio.com/_apis/public/gallery/publishers/${fieldA}/vsextensions/${fieldB}/${version}/vspackage
   ```

   Will get the final URL as:
   ```bash
   https://marketplace.visualstudio.com/_apis/public/gallery/publishers/denoland/vsextensions/vscode-deno/3.43.3/vspackage
   ```

7. Paste the final URL into your browser and press Enter to begin the download.