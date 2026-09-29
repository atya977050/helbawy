class AbqarynoChat {
    constructor() {
        this.messages = [];
    }

    send(message) {
        const text = String(message || "").trim();

        if (!text) {
            return null;
        }

        const item = {
            id: Date.now(),
            text,
            created_at: new Date().toISOString()
        };

        this.messages.push(item);

        document.dispatchEvent(
            new CustomEvent("abqaryno:message", {
                detail: item
            })
        );

        return item;
    }

    getMessages() {
        return [...this.messages];
    }
}

window.AbqarynoChat = AbqarynoChat;
window.abqarynoChat = new AbqarynoChat();
