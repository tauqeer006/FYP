let video = document.getElementById("camera");
let output = document.getElementById("output");
let reps = document.getElementById("reps");
let stage = document.getElementById("stage");

document.getElementById("startBtn").onclick = async () => {
    // Open camera in browser
    let stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;

    // Start sending frames to FastAPI
    processFrames();
};

async function processFrames() {
    let canvas = document.createElement("canvas");
    let ctx = canvas.getContext("2d");

    canvas.width = 640;
    canvas.height = 480;

    setInterval(async () => {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async blob => {
            let formData = new FormData();
            formData.append("file", blob, "frame.jpg");

            let res = await fetch("/process_frame", {
                method: "POST",
                body: formData,
            });

            let data = await res.json();

            // Show processed frame
            output.src = "data:image/jpeg;base64," + data.frame;

            // Update info
            reps.innerText = data.counter;
            stage.innerText = data.stage;
        });
    }, 150); // ~7 FPS
}
