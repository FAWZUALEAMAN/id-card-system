let holders = [];

// Load holders on page load
$(document).ready(function() {
    loadHolders();
    
    // Photo preview
    $('#photo').change(function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#photoPreview').html(`<img src="${e.target.result}" class="img-fluid">`);
            };
            reader.readAsDataURL(file);
        }
    });
    
    // Save holder
    $('#saveHolderBtn').click(saveHolder);
    
    // Search functionality
    $('#searchInput').on('input', filterCards);
    $('#deptFilter').on('change', filterCards);
    
    // Bulk import
    $('#importCSVBtn').click(bulkImport);
    $('#downloadSample').click(downloadSample);
    $('#exportCSVBtn').click(exportToCSV);
});

async function loadHolders() {
    try {
        const response = await fetch('/api/holders');
        holders = await response.json();
        updateStats();
        populateDepartmentFilter();
        displayCards();
    } catch (error) {
        console.error('Error loading holders:', error);
    }
}

function updateStats() {
    $('#totalCards').text(holders.length);
    const uniqueDepts = new Set(holders.map(h => h.department));
    $('#totalDept').text(uniqueDepts.size);
    const active = holders.filter(h => h.status === 'active').length;
    $('#activeCards').text(active);
    $('#totalGen').text(holders.length);
}

function populateDepartmentFilter() {
    const depts = [...new Set(holders.map(h => h.department))];
    const filter = $('#deptFilter');
    depts.forEach(dept => {
        filter.append(`<option value="${dept}">${dept}</option>`);
    });
}

function filterCards() {
    displayCards();
}

function displayCards() {
    const searchTerm = $('#searchInput').val().toLowerCase();
    const deptFilter = $('#deptFilter').val();
    
    const filtered = holders.filter(holder => {
        const matchSearch = holder.full_name.toLowerCase().includes(searchTerm) ||
                           holder.employee_id.toLowerCase().includes(searchTerm) ||
                           holder.department.toLowerCase().includes(searchTerm);
        const matchDept = !deptFilter || holder.department === deptFilter;
        return matchSearch && matchDept;
    });
    
    const container = $('#cardsContainer');
    container.empty();
    
    if (filtered.length === 0) {
        container.html('<div class="col-12 text-center"><h3>No ID Cards Found</h3></div>');
        return;
    }
    
    filtered.forEach(holder => {
        const card = `
            <div class="col-md-4 col-lg-3 mb-4">
                <div class="id-card">
                    <div class="card-preview">
                        <img src="${holder.photo || 'https://via.placeholder.com/100'}" class="card-avatar" alt="${holder.full_name}">
                        <div class="card-info mt-3">
                            <h5>${holder.full_name}</h5>
                            <small>${holder.employee_id}</small>
                            <p class="mt-2 mb-0"><strong>${holder.department}</strong></p>
                            <small>${holder.designation}</small>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-sm btn-primary" onclick="generateCard('${holder.id}')">
                            <i class="fas fa-download"></i> Generate
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteHolder('${holder.id}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.append(card);
    });
}

async function saveHolder() {
    const photoFile = $('#photo')[0].files[0];
    let photoUrl = '';
    
    if (photoFile) {
        const formData = new FormData();
        formData.append('photo', photoFile);
        
        try {
            const uploadRes = await fetch('/api/upload-photo', {
                method: 'POST',
                body: formData
            });
            const uploadData = await uploadRes.json();
            photoUrl = uploadData.photo_url;
        } catch (error) {
            alert('Error uploading photo');
            return;
        }
    }
    
    const holderData = {
        full_name: $('#fullName').val(),
        employee_id: $('#employeeId').val(),
        department: $('#department').val(),
        designation: $('#designation').val(),
        email: $('#email').val(),
        phone: $('#phone').val(),
        blood_group: $('#bloodGroup').val(),
        photo: photoUrl
    };
    
    try {
        const response = await fetch('/api/holders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(holderData)
        });
        
        if (response.ok) {
            alert('ID Card created successfully!');
            $('#addCardModal').modal('hide');
            $('#holderForm')[0].reset();
            $('#photoPreview').empty();
            loadHolders();
        } else {
            alert('Error creating ID card');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error creating ID card');
    }
}

async function generateCard(holderId) {
    try {
        window.open(`/api/generate-card/${holderId}`, '_blank');
    } catch (error) {
        alert('Error generating card');
    }
}

async function deleteHolder(holderId) {
    if (confirm('Are you sure you want to delete this ID card?')) {
        try {
            const response = await fetch(`/api/holders/${holderId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                loadHolders();
            } else {
                alert('Error deleting card');
            }
        } catch (error) {
            alert('Error deleting card');
        }
    }
}

async function bulkImport() {
    const file = $('#csvFile')[0].files[0];
    if (!file) {
        alert('Please select a CSV file');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = async function(e) {
        const csv = e.target.result;
        const lines = csv.split('\n');
        const headers = lines[0].split(',');
        const holders = [];
        
        for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim()) {
                const values = lines[i].split(',');
                const holder = {};
                headers.forEach((header, index) => {
                    holder[header.trim()] = values[index]?.trim() || '';
                });
                holders.push(holder);
            }
        }
        
        try {
            const response = await fetch('/api/bulk-import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ holders })
            });
            
            if (response.ok) {
                alert(`Successfully imported ${holders.length} ID cards!`);
                $('#bulkImportModal').modal('hide');
                loadHolders();
            } else {
                alert('Error importing cards');
            }
        } catch (error) {
            alert('Error importing cards');
        }
    };
    reader.readAsText(file);
}

function downloadSample() {
    const sample = `full_name,employee_id,department,designation,email\nJohn Doe,EMP001,IT,Software Engineer,john@example.com\nJane Smith,EMP002,HR,HR Manager,jane@example.com`;
    const blob = new Blob([sample], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_id_cards.csv';
    a.click();
    URL.revokeObjectURL(url);
}

function exportToCSV() {
    const headers = ['full_name', 'employee_id', 'department', 'designation', 'email', 'phone', 'blood_group'];
    const csvRows = [headers.join(',')];
    
    holders.forEach(holder => {
        const row = headers.map(header => `"${holder[header] || ''}"`);
        csvRows.push(row.join(','));
    });
    
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'id_cards_export.csv';
    a.click();
    URL.revokeObjectURL(url);
}