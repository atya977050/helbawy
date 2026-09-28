
const socket = io();
io.on("connection", (socket) => {
    socket.on("webrtc:offer", (offer) => {
        socket.broadcast.emit("webrtc:offer", offer);
    });

    socket.on("webrtc:answer", (answer) => {
        socket.broadcast.emit("webrtc:answer", answer);
    });

    socket.on("webrtc:ice-candidate", (candidate) => {
        socket.broadcast.emit("webrtc:ice-candidate", candidate);
    });
});
let localStream, remoteStream, peerConnection;
const servers = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };
peerConnection = new RTCPeerConnection(servers);
async function init() {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));
}
init();
async function createOffer() {
    if (!peerConnection) {
        throw new Error("PeerConnection is not initialized.");
    }

    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    socket.emit("webrtc:offer", offer);
}

async function handleOffer(offer) {
    if (!peerConnection) {
        throw new Error("PeerConnection is not initialized.");
    }

    await peerConnection.setRemoteDescription(
        new RTCSessionDescription(offer)
    );

    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    socket.emit("webrtc:answer", answer);
}

async function handleAnswer(answer) {
    if (!peerConnection) {
        throw new Error("PeerConnection is not initialized.");
    }

    await peerConnection.setRemoteDescription(
        new RTCSessionDescription(answer)
    );
}

peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
        socket.emit("webrtc:ice-candidate", event.candidate);
    }
};

socket.on("webrtc:offer", handleOffer);
socket.on("webrtc:answer", handleAnswer);

socket.on("webrtc:ice-candidate", async (candidate) => {
    if (!peerConnection || !candidate) {
        return;
    }

    await peerConnection.addIceCandidate(
        new RTCIceCandidate(candidate)
    );
});

 peerConnection.ontrack = (e) => { remoteVideo.srcObject = e.streams[0]; };