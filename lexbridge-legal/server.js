const express = require("express");
const app = express();
app.use(express.json());
app.get("/api/health", (req, res) => res.json({ ok: true, status: "PASS" }));
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
