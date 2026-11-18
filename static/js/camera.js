// Camera snapshot utility for AI Food Nutrition Analyzer

let videoStream = null;

function startCamera() {
    const video = document.getElementById('cameraVideo');
    const cameraSection = document.getElementById('cameraSection');
    const uploadSection = document.getElementById('uploadSection');
    const startCamBtn = document.getElementById('startCamBtn');
    const stopCamBtn = document.getElementById('stopCamBtn');
    const snapBtn = document.getElementById('snapBtn');

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Camera access is not supported by your browser or environment.");
        return;
    }

    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(stream => {
            videoStream = stream;
            video.srcObject = stream;
            video.play();
            cameraSection.classList.remove('d-none');
            if (uploadSection) uploadSection.classList.add('d-none');
            if (startCamBtn) startCamBtn.classList.add('d-none');
            if (stopCamBtn) stopCamBtn.classList.remove('d-none');
            if (snapBtn) snapBtn.classList.remove('d-none');
        })
        .catch(err => {
            console.error("Camera access error:", err);
            alert("Unable to access camera: " + err.message + ". Please ensure camera permissions are granted or use the file upload option.");
        });
}

function captureSnapshot() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('captureCanvas');
    const cameraDataInput = document.getElementById('camera_data');
    const imagePreview = document.getElementById('imagePreview');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const retakeBtn = document.getElementById('retakeBtn');
    const snapBtn = document.getElementById('snapBtn');

    if (!video || !canvas || !cameraDataInput) return;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    cameraDataInput.value = dataUrl;

    if (imagePreview) {
        imagePreview.src = dataUrl;
        imagePreview.classList.remove('d-none');
    }
    if (uploadPlaceholder) uploadPlaceholder.classList.add('d-none');

    // Freeze video display
    video.pause();
    if (snapBtn) snapBtn.classList.add('d-none');
    if (retakeBtn) retakeBtn.classList.remove('d-none');
}

function retakeSnapshot() {
    const video = document.getElementById('cameraVideo');
    const cameraDataInput = document.getElementById('camera_data');
    const retakeBtn = document.getElementById('retakeBtn');
    const snapBtn = document.getElementById('snapBtn');

    cameraDataInput.value = '';
    if (video) video.play();
    if (snapBtn) snapBtn.classList.remove('d-none');
    if (retakeBtn) retakeBtn.classList.add('d-none');
}

function stopCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    const cameraSection = document.getElementById('cameraSection');
    const uploadSection = document.getElementById('uploadSection');
    const startCamBtn = document.getElementById('startCamBtn');
    const stopCamBtn = document.getElementById('stopCamBtn');
    const snapBtn = document.getElementById('snapBtn');
    const retakeBtn = document.getElementById('retakeBtn');

    if (cameraSection) cameraSection.classList.add('d-none');
    if (uploadSection) uploadSection.classList.remove('d-none');
    if (startCamBtn) startCamBtn.classList.remove('d-none');
    if (stopCamBtn) stopCamBtn.classList.add('d-none');
    if (snapBtn) snapBtn.classList.add('d-none');
    if (retakeBtn) retakeBtn.classList.add('d-none');
}
