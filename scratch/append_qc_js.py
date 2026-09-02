import re

js_code = """
    function openQCReportModal() {
        document.getElementById('modal-qc-print').classList.add('active');
    }

    function closeQCReportModal() {
        document.getElementById('modal-qc-print').classList.remove('active');
        document.getElementById('qc-print-model').value = '';
        document.getElementById('qc-print-serial').value = '';
    }

    function submitQCReportPrint() {
        const model = document.getElementById('qc-print-model').value.trim();
        const serial = document.getElementById('qc-print-serial').value.trim();
        if (!model || !serial) {
            alert('Please enter both Model Code and Serial Number');
            return;
        }
        
        const url = `/admin/print-specific-qc?model=${encodeURIComponent(model)}&serial=${encodeURIComponent(serial)}`;
        window.open(url, '_blank');
        closeQCReportModal();
    }
"""

with open('app/templates/admin/components/scripts.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('</script>', js_code + '\n</script>')

with open('app/templates/admin/components/scripts.html', 'w', encoding='utf-8') as f:
    f.write(content)
