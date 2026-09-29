const express = require("express");
const Database = require("better-sqlite3");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(express.json());

const dbPath = path.join(__dirname, "database", "app.db");
const db = new Database(dbPath);
const schema = fs.readFileSync(path.join(__dirname, "database", "schema.sql"), "utf8");
db.exec(schema);

app.get("/api/health", (req, res) => res.json({ ok: true, status: "PASS", factory: "Abqaryno Master" }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Abqaryno App running on port ${PORT}`));
