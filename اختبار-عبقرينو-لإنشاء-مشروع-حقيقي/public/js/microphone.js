class AbqarynoMicrophone {
    constructor() {
        this.stream = null;
        this.recorder = null;
        this.chunks = [];
    }

    async start() {
        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error("المايك غير مدعوم في هذا المتصفح");
        }

        this.stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        return this.stream;
    }

    record() {
        if (!this.stream) {
            throw new Error("شغّل المايك أولًا");
        }

        this.chunks = [];
        this.recorder = new MediaRecorder(this.stream);

        this.recorder.ondataavailable = event => {
            if (event.data.size > 0) {
                this.chunks.push(event.data);
            }
        };

        this.recorder.start();
    }

    stopRecording() {
        return new Promise(resolve => {
            if (!this.recorder) {
                resolve(null);
                return;
            }

            this.recorder.onstop = () => {
                const blob = new Blob(
                    this.chunks,
                    { type: "audio/webm" }
                );

                resolve(blob);
            };

            this.recorder.stop();
        });
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(
                track => track.stop()
            );
        }

        this.stream = null;
        this.recorder = null;
    }
}

window.AbqarynoMicrophone = AbqarynoMicrophone;
