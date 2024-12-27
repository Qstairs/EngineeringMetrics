document.addEventListener('DOMContentLoaded', function() {
    const markdownInput = document.getElementById('markdownInput');
    const preview = document.getElementById('preview');

    function updatePreview() {
        const markdown = markdownInput.value;
        fetch('/api/preview_markdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: markdown })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                preview.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            } else {
                preview.innerHTML = data.html;
            }
        })
        .catch(error => {
            preview.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        });
    }

    // Add debounce to prevent too many requests
    let timeoutId;
    markdownInput.addEventListener('input', () => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(updatePreview, 300);
    });

    // Initial preview
    updatePreview();
});
