class AbqarynoCamera {
    constructor() {
        this.stream = null;
    }

    async start(videoElement) {
        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error("الكاميرا غير مدعومة في هذا المتصفح");
        }

        this.stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

        if (videoElement) {
            videoElement.srcObject = this.stream;
            videoElement.autoplay = true;
            videoElement.playsInline = true;
        }

        return this.stream;
    }

    stop() {
        if (!this.stream) {
            return;
        }

        this.stream.getTracks().forEach(
            track => track.stop()
        );

        this.stream = null;
    }
}

window.AbqarynoCamera = AbqarynoCamera;
