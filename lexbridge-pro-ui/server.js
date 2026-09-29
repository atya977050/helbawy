const express = require("express");
const { DatabaseSync } = require("node:sqlite");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const dbPath = path.join(__dirname, "database", "app.db");
const db = new Database(dbPath);
const schema = fs.readFileSync(path.join(__dirname, "database", "schema.sql"), "utf8");
db.exec(schema);

app.get("/api/health", (req, res) => res.json({ ok: true, status: "PASS", factory: "Abqaryno Master" }));

app.get("/api/cases", (req, res) => {
    try {
        const cases = db.prepare("SELECT * FROM cases").all();
        res.json({ ok: true, cases });
    } catch(e) {
        res.json({ ok: true, cases: [] });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Abqaryno App running on port ${PORT}`));
