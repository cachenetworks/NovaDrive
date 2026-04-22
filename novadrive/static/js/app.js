const toastDismissDelay = 5000;

function initToasts() {
  document.querySelectorAll("[data-toast]").forEach((toast) => {
    const closeButton = toast.querySelector("[data-dismiss-toast]");
    const dismiss = () => {
      toast.classList.add("translate-x-4", "opacity-0");
      setTimeout(() => toast.remove(), 180);
    };

    closeButton?.addEventListener("click", dismiss);
    window.setTimeout(dismiss, toastDismissDelay);
  });
}

function initConfirmModal() {
  const modal = document.getElementById("confirm-modal");
  if (!modal) return;

  const titleEl = document.getElementById("confirm-modal-title");
  const bodyEl = document.getElementById("confirm-modal-body");
  const confirmButton = document.getElementById("confirm-modal-submit");
  const cancelButton = modal.querySelector("[data-confirm-cancel]");
  let pendingForm = null;

  const closeModal = () => {
    modal.classList.add("hidden");
    modal.classList.remove("flex", "pointer-events-auto");
    modal.classList.add("pointer-events-none");
    pendingForm = null;
  };

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-confirm-submit]");
    if (!trigger) return;

    event.preventDefault();
    pendingForm = trigger.closest("form");
    titleEl.textContent = trigger.dataset.confirmTitle || "Confirm action";
    bodyEl.textContent = trigger.dataset.confirmBody || "This action cannot be undone.";
    modal.classList.remove("hidden", "pointer-events-none");
    modal.classList.add("flex", "pointer-events-auto");
  });

  confirmButton?.addEventListener("click", () => {
    if (pendingForm) pendingForm.submit();
    closeModal();
  });

  cancelButton?.addEventListener("click", closeModal);
  modal.addEventListener("click", (event) => {
    if (event.target === modal || event.target === modal.firstElementChild) {
      closeModal();
    }
  });
}

function toastMessage(message, variant = "info") {
  const container = document.createElement("div");
  container.className = "pointer-events-auto rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur-xl";

  if (variant === "success") {
    container.classList.add("border-emerald-400/30", "bg-emerald-500/15", "text-emerald-100");
  } else if (variant === "error") {
    container.classList.add("border-rose-400/30", "bg-rose-500/15", "text-rose-100");
  } else {
    container.classList.add("border-fuchsia-400/30", "bg-fuchsia-500/15", "text-fuchsia-100");
  }

  container.innerHTML = `
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="text-sm font-semibold">${variant[0].toUpperCase() + variant.slice(1)}</p>
        <p class="mt-1 text-sm leading-6">${message}</p>
      </div>
      <button type="button" class="text-sm text-white/60 transition hover:text-white" data-dismiss-toast>&times;</button>
    </div>
  `;

  let stack = document.querySelector("[data-runtime-toast-stack]");
  if (!stack) {
    stack = document.createElement("div");
    stack.className = "pointer-events-none fixed right-4 top-4 z-[85] flex w-full max-w-sm flex-col gap-3";
    stack.dataset.runtimeToastStack = "true";
    document.body.appendChild(stack);
  }

  stack.appendChild(container);
  const dismissButton = container.querySelector("[data-dismiss-toast]");
  const dismiss = () => {
    container.classList.add("translate-x-4", "opacity-0");
    setTimeout(() => container.remove(), 180);
  };
  dismissButton?.addEventListener("click", dismiss);
  setTimeout(dismiss, toastDismissDelay);
}

function initCopyButtons() {
  document.querySelectorAll("[data-copy-text]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copyText || "");
        toastMessage("Share link copied to clipboard.", "success");
      } catch (error) {
        toastMessage("Could not copy that link automatically.", "error");
      }
    });
  });
}

function initUploads() {
  document.querySelectorAll("[data-upload-form]").forEach((form) => {
    const dropzone = form.querySelector("[data-upload-dropzone]");
    const input = form.querySelector("[data-upload-input]");
    const progressShell = form.querySelector("[data-upload-progress-shell]");
    const progressBar = form.querySelector("[data-upload-progress]");
    const status = form.querySelector("[data-upload-status]");

    if (!dropzone || !input || !progressShell || !progressBar || !status) return;

    const setFiles = (files) => {
      input.files = files;
      if (files.length > 0) {
        status.textContent = `${files.length} file(s) ready to upload.`;
      }
    };

    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add("border-fuchsia-300/70", "bg-fuchsia-500/15");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove("border-fuchsia-300/70", "bg-fuchsia-500/15");
      });
    });

    dropzone.addEventListener("drop", (event) => {
      const fileList = event.dataTransfer?.files;
      if (!fileList || fileList.length === 0) return;
      const transfer = new DataTransfer();
      Array.from(fileList).forEach((file) => transfer.items.add(file));
      setFiles(transfer.files);
    });

    input.addEventListener("change", () => {
      if (input.files?.length) {
        status.textContent = `${input.files.length} file(s) ready to upload.`;
      }
    });

    form.addEventListener("submit", (event) => {
      if (form.dataset.ajaxUpload !== "true") return;
      event.preventDefault();

      if (!input.files || input.files.length === 0) {
        toastMessage("Choose at least one file before uploading.", "error");
        return;
      }

      const xhr = new XMLHttpRequest();
      xhr.open("POST", form.action);
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

      progressShell.classList.remove("hidden");
      progressBar.style.width = "0%";
      status.textContent = "Preparing upload...";

      xhr.upload.addEventListener("progress", (progressEvent) => {
        if (!progressEvent.lengthComputable) return;
        const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
        progressBar.style.width = `${percent}%`;
        status.textContent = `Uploading... ${percent}%`;
      });

      xhr.addEventListener("load", () => {
        try {
          const payload = JSON.parse(xhr.responseText);
          if (xhr.status >= 200 && xhr.status < 300 && payload.success) {
            toastMessage(`Uploaded ${payload.uploaded.length} file(s) successfully.`, "success");
            status.textContent = "Upload complete. Refreshing view...";
            window.setTimeout(() => window.location.reload(), 700);
          } else {
            throw new Error(payload.error || "Upload failed.");
          }
        } catch (error) {
          toastMessage(error.message, "error");
          status.textContent = "Upload failed.";
        }
      });

      xhr.addEventListener("error", () => {
        toastMessage("Upload failed unexpectedly.", "error");
        status.textContent = "Upload failed.";
      });

      xhr.send(new FormData(form));
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initToasts();
  initConfirmModal();
  initCopyButtons();
  initUploads();
});
