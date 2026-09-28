
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const app = express();
const server = http.createServer(app);
const io = new Server(server);
app.use(express.static('public'));
server.listen(3000, () => console.log('Server running on port 3000'));
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
