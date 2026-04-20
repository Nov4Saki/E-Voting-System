/* ============================================================
   VOTESEC — MAIN SCRIPT
   Handles: Registration validation, image preview, voting flow
   ============================================================ */

'use strict';

/* ──────────────────────────────────────────
   REGISTRATION PAGE
────────────────────────────────────────── */
(function initRegistration() {
    const form = document.getElementById('registrationForm');
    if (!form) return;  // Not on registration page

    const idUpload = document.getElementById('idUpload');
    const selfieUpload = document.getElementById('selfieUpload');
    const idPreview = document.getElementById('idPreview');
    const selfiePreview = document.getElementById('selfiePreview');
    const idZone = document.getElementById('idZone');
    const selfieZone = document.getElementById('selfieZone');


    /* ── Image Preview Handler ── */
    function setupPreview(input, preview, zone) {
        input.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
                preview.style.display = 'block';
                // Hide the placeholder icon/text when preview is shown
                zone.querySelectorAll('.upload-icon, strong, p:not(.img-preview)')
                    .forEach(el => el.style.opacity = '0.4');
            };
            reader.readAsDataURL(file);
        });

        // Drag-over visual feedback
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                const dt = new DataTransfer();
                dt.items.add(file);
                input.files = dt.files;
                input.dispatchEvent(new Event('change'));
            }
        });
    }

    setupPreview(idUpload, idPreview, idZone);
    setupPreview(selfieUpload, selfiePreview, selfieZone);


    /* ── Registration Validation Logic ── */
    const ALLOWED_EXTENSIONS = ['image/jpeg', 'image/png', 'image/webp'];
    const MAX_SIZE_MB = 10;
    const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;


    /* ── Form Submit ── */
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const idFile = idUpload.files[0];
        const selfieFile = selfieUpload.files[0];

        // 1. Check if something is missing
        if (!idFile || !selfieFile) {
            showErrorModal({
                title: 'Missing Documents',
                icon: 'bi-file-earmark-x',
                type: 'danger',
                msg: 'Please upload both your National ID image and a selfie holding your ID before submitting.'
            });
            return;
        }

        // 2. Check if extension is valid
        if (!ALLOWED_EXTENSIONS.includes(idFile.type) || !ALLOWED_EXTENSIONS.includes(selfieFile.type)) {
            showErrorModal({
                title: 'Invalid File Type',
                icon: 'bi-exclamation-octagon-fill',
                type: 'danger',
                msg: 'Only JPG, PNG, and WEBP images are allowed. Please check your files and try again.'
            });
            return;
        }

        // 3. Check if size is too large
        if (idFile.size > MAX_SIZE_BYTES || selfieFile.size > MAX_SIZE_BYTES) {
            showErrorModal({
                title: 'File Too Large',
                icon: 'bi-shield-x',
                type: 'danger',
                msg: `One or more files exceed the ${MAX_SIZE_MB}MB limit. Please compress your images or use a different file.`
            });
            return;
        }

        // If all checks pass, proceed with real submission
        const btn = document.getElementById('registerBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';

        // Submit the form for real
        form.submit();
    });


    /* ── Show Error Modal ── */
    function showErrorModal({ title, icon, type, msg }) {
        const titleEl = document.getElementById('errorModalTitle');
        const msgEl = document.getElementById('errorModalMsg');
        const iconEl = document.getElementById('modalIcon');

        if (titleEl) titleEl.textContent = title;
        if (msgEl) msgEl.textContent = msg;

        if (iconEl) {
            iconEl.className = `modal-icon ${type}`;
            iconEl.innerHTML = `<i class="bi ${icon}"></i>`;
        }

        const modalEl = document.getElementById('errorModal');
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        }
    }

})();


/* ──────────────────────────────────────────
   VOTING PAGE 
────────────────────────────────────────── */
(function initVoting() {
    const confirmModalEl = document.getElementById('voteConfirmModal');
    if (!confirmModalEl) return;

    const confirmBtn = document.getElementById('confirmVoteBtn');
    const confirmText = document.getElementById('voteConfirmText');
    const bsConfirm = new bootstrap.Modal(confirmModalEl);

    let targetAction = ""; // Will store "Vote1" or "Vote2"

    /* 1. OPEN MODAL */
    window.openVoteModal = function (candidateName, actionName) {
        targetAction = actionName;

        if (confirmText) {
            confirmText.innerHTML = `Are you sure you want to vote for <strong>${candidateName}</strong>?`;
        }

        bsConfirm.show();
    };

    /* 2. CONFIRM ACTION */
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function () {
            if (targetAction) {
                window.location.href = `/Vote/${targetAction}`;
            }
        });
    }
})();
