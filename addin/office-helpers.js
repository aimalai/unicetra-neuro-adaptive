// office-helpers.js

export async function getSelectedText() {
  return new Promise((resolve, reject) => {
    Office.context.document.getSelectedDataAsync(
      Office.CoercionType.Text,
      (result) => {
        if (result.status === Office.AsyncResultStatus.Succeeded) {
          resolve(result.value);
        } else {
          reject(result.error.message);
        }
      },
    );
  });
}

export function writeTextToDocument(textToInject) {
  Office.context.document.setSelectedDataAsync(
    textToInject,
    { coercionType: Office.CoercionType.Text },
    (result) => {
      if (result.status === Office.AsyncResultStatus.Failed) {
        console.error("Failed to update Word doc: " + result.error.message);
      }
    },
  );
}

export async function highlightTextInDocument(searchString, color = "yellow") {
  return Word.run(async (context) => {
    // Search the document body for the failing sentence
    const searchResults = context.document.body.search(searchString.trim(), {
      matchCase: false,
      matchWholeWord: false,
      ignoreSpace: true,
    });

    searchResults.load("font");
    await context.sync();

    // Apply the highlight color to every instance found
    for (let i = 0; i < searchResults.items.length; i++) {
      searchResults.items[i].font.highlightColor = color;
    }

    await context.sync();
  }).catch(function (error) {
    console.error("Failed to highlight text in Word: " + error);
  });
}

export async function insertCommentAtSelection(commentText) {
  return Word.run(async (context) => {
    // Get the exact text the user highlighted
    const range = context.document.getSelection();

    // Attach a marginal comment to that specific range
    range.insertComment(commentText);

    await context.sync();
  }).catch(function (error) {
    console.error("Failed to insert comment in Word: " + error);
  });
}

// Add these to office-helpers.js
export async function getFullDocumentText() {
  return Word.run(async (context) => {
    const body = context.document.body;
    body.load("text");
    await context.sync();
    return body.text;
  }).catch(function (error) {
    console.error("Failed to read full document: " + error);
  });
}

export async function replaceFullDocumentText(newText) {
  return Word.run(async (context) => {
    // If the backend pruned 100% of the text, insertText("") might crash Word.
    // We provide a fallback space character just to be safe.
    const safeText = newText === "" ? " " : newText;

    context.document.body.insertText(safeText, "Replace");
    await context.sync();
  }).catch(function (error) {
    console.error("Failed to replace document text: " + error);
  });
}
