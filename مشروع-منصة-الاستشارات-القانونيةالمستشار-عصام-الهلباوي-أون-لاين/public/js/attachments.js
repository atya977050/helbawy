class AbqarynoAttachments {
    constructor() {
        this.files = [];
    }

    add(fileList) {
        const files = Array.from(fileList || []);

        this.files.push(...files);

        document.dispatchEvent(
            new CustomEvent("abqaryno:attachments", {
                detail: files
            })
        );

        return files;
    }

    clear() {
        this.files = [];
    }

    getFiles() {
        return [...this.files];
    }
}

window.AbqarynoAttachments = AbqarynoAttachments;
window.abqarynoAttachments = new AbqarynoAttachments();
