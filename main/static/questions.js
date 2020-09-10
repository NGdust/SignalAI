window.onload = function () {
    document.getElementsByClassName("title")[0].innerText = 'Upload audio file'
    document.querySelector("select").addEventListener('change', function (e) {
        if (e.target.value === '1') {
            document.querySelector("#text1").style.display = ''
            document.querySelector("#file").style.display = 'None'
            document.querySelector("#mic").style.display = 'None'
            document.querySelector("#replyBtn").style.display = ''
        } else if (e.target.value === '2') {
            document.querySelector("#file").style.display = ''
            document.querySelector("#text1").style.display = 'None'
            document.querySelector("#mic").style.display = 'None'
            document.querySelector("#replyBtn").style.display = ''
        } else {
            document.querySelector("#file").style.display = 'None'
            document.querySelector("#text1").style.display = 'None'
            document.querySelector("#mic").style.display = ''
            document.querySelector("#replyBtn").style.display = 'None'
            newRecorder()
        }
    })


    if (document.getElementById("tipMessage").innerText) {
        document.getElementById("selectTypeInput").style.display = 'None'
        document.querySelector('#checkSizeInputText').style.display = 'None'
    } else {
        document.getElementById("selectTypeInput").style.display = ''
    }
}

// Счетчик символов
const s = 100
document.querySelector('#text').addEventListener('input', function (e) {
    if (!document.getElementById("tipMessage").innerText) {
        if (e.target.value.length > s) {
            document.querySelector('#checkSizeInputText').style.display = 'None'
        } else {
            document.querySelector('#checkSizeInputText').style.display = ''
            document.querySelector('#checkSizeInputText').innerText = '«Please tell us more about your problem...» ' + e.target.value.length + ' -- ' + s
        }
    }
})

function clearFileInput(id) {
    var oldInput = document.getElementById(id);

    var newInput = document.createElement("input");

    newInput.type = "file";
    newInput.id = oldInput.id;
    newInput.name = oldInput.name;
    newInput.className = oldInput.className;
    newInput.style.cssText = oldInput.style.cssText;
    newInput.onchange = oldInput.onchange
    newInput.accept = oldInput.accept
    oldInput.parentNode.replaceChild(newInput, oldInput);
}


function apiRequest() {
    document.getElementById("container").style.display = 'block'
    document.getElementById("question").style.display = 'None'
    document.getElementById('errorMessage').style.display = 'None'
    document.getElementById("answerBlock").style.display = 'None'
    document.getElementById("inputBlock").style.display = 'None'
    document.getElementById("resultInfo").style.display = 'None'
    document.getElementById("tipMessage").innerText = ''


    let count = 0 // Счетчик запросов
    let timerId = setTimeout(function tick() {
        const cookies = document.cookie;
        $.ajax(
            {
                type: "POST",
                url: "/updateQuestion",
                data: {
                    "cookies": cookies,
                    "url": document.location.pathname,
                },
                dataType: "text",
                cache: false,
                success: function (data) {
                    console.log(data)
                    console.log(count)
                    if (count === 10) {
                        document.getElementById('errorMessage').innerText = 'Too long waiting for the server. Try it one more time.!!!'
                        document.getElementById('errorMessage').style.display = ''
                        document.getElementById("question").style.display = ''
                        document.getElementById("container").style.display = 'None'
                        document.getElementById("inputBlock").style.display = ''
                        clearTimeout(timerId)
                    }
                    if (data !== "false") {
                        const res = JSON.parse(data)
                        console.log(res)
                        if (res['errorMessage']) {
                            document.getElementById("question").style.display = ''
                            document.getElementById("inputBlock").style.display = ''
                            document.getElementById('errorMessage').style.display = ''
                            document.getElementById("container").style.display = 'None'

                            document.getElementById('question').innerHTML = "<span style='font-size: 25px; font-weight: bold; margin-right: 20px'>Question:</span> <span>" + res['question'] + "</span>"
                            document.getElementById('errorMessage').innerText = res['errorMessage']
                            clearTimeout(timerId)
                            return
                        }
                        document.getElementById('question').innerHTML = "<span style='font-size: 25px; font-weight: bold; margin-right: 20px'>Question:</span> <span>" + res['question'] + "</span>"
                        document.getElementById("container").style.display = 'None'
                        document.getElementById('errorMessage').style.display = 'None'
                        document.getElementById("question").style.display = ''
                        document.getElementById("inputBlock").style.display = ''
                        if (res['tipMessage']) {
                            document.getElementById("tipMessage").innerText = res['tipMessage']
                            document.getElementById("selectTypeInput").style.display = 'None'

                        } else {
                            document.getElementById("selectTypeInput").style.display = ''
                            document.querySelector('#checkSizeInputText').style.display = 'None'
                        }
                        if (res['maxEmotions']) {
                            document.getElementById("resultInfo").style.display = ''
                            document.getElementById("lastResultSymbl").innerText = ''
                            document.getElementById("lastResultEmoshape").innerHTML = '3 emotions - ' + res['maxEmotions']
                            if (res['symblTopics']) {
                                document.getElementById("lastResultSymbl").innerText = 'Topics from Symbl AI - ' + res['symblTopics']
                            }
                        }
                        if (res['answerCategory']) {
                            document.getElementById("question").style.display = 'None'
                            document.getElementById("inputBlock").style.display = 'None'
                            document.getElementById("answerBlock").style.display = 'block'
                            document.getElementById("answerBlock").innerText = res['answerCategory']
                        }
                        clearTimeout(timerId)
                    }
                },
            });
        count++
        timerId = setTimeout(tick, 5000); // (*)

    }, 0);


}

function submit() {
    const text = document.getElementById("text").value
    const file = document.getElementById("file2").files[0]

    // Ошибка если пустые поля
    if (!text && !file) {
        document.getElementById('errorMessage').style.display = ''
        document.getElementById('errorMessage').innerText = 'Error: not input'
        return
    }

    // Формирует данные для отправки на сервер
    const formdata = new FormData();
    formdata.append("text", text)
    formdata.append("file", file)

    // Отправка на сервер
    var xhr = new XMLHttpRequest();
    xhr.open('POST', document.location.pathname, true);
    xhr.send(formdata);

    // Очищаем поля ввода
    document.getElementById("text").value = ''
    clearFileInput("file2")

    // Начать опрашивать сервер на результат
    apiRequest()
}

function renameLabelFileInput(event) {

    const newFile = event.split('\\').find((item, idx, arr) => idx === arr.length - 1);
    document.getElementsByClassName("title")[0].innerText = newFile;
}


// Запись аудио
function newRecorder() {
    navigator.mediaDevices.getUserMedia({audio: true})
        .then(stream => {
            const mediaRecorder = new MediaRecorder(stream);

            document.querySelector('#startRec').addEventListener('click', function () {
                document.querySelector('#progressRec').style.animation = 'radial-pulse 1s infinite'
                mediaRecorder.start();
            });

            let audioChunks = [];

            mediaRecorder.ondataavailable = function (e) {
                audioChunks.push(e.data);
            }


            mediaRecorder.addEventListener("stop", function () {

                const audioBlob = new Blob(audioChunks, {
                    type: 'audio/wav'
                });

                // Отправка на сервер
                const formdata = new FormData();
                formdata.append("file", audioBlob)
                var xhr = new XMLHttpRequest();
                xhr.open('POST', document.location.pathname, true);
                xhr.send(formdata);

                apiRequest()
                audioChunks = []
            });

            document.querySelector('#stopRec').addEventListener('click', function () {
                document.querySelector('#progressRec').style.animation = ''
                mediaRecorder.stop();
            });
        });
}