document.querySelector("#outEmotion").addEventListener('change', function () {
    fetch('/updateUser', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({outEmotionList: this.checked, cookies: document.cookie}),
    })
})