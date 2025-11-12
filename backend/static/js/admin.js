let userToDelete = null;
let editing = false;

document.addEventListener('DOMContentLoaded', function () {
  loadUsers();
  loadSystemStats();
  loadAllLogs();

  // animations
  const cards = document.querySelectorAll('.card');
  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
    card.classList.add('fade-in');
  });
});

// -------- navigation between sections ----------
function showSection(sectionId) {
  document.querySelectorAll('.dashboard-section').forEach(sec => sec.classList.remove('active'));
  const selected = document.getElementById(sectionId);
  if (selected) selected.classList.add('active');
}

// -------------------- stats --------------------
async function loadSystemStats() {
  try {
    const [usersResponse, logsResponse] = await Promise.all([
      fetch('/api/users', { credentials: 'include' }),
      fetch('/api/stress-logs', { credentials: 'include' })
    ]);

    const usersData = await usersResponse.json();
    const logsData = await logsResponse.json();

    document.getElementById('totalUsers').textContent =
      usersData.success ? usersData.users.length : '0';
    document.getElementById('totalSessions').textContent =
      logsData.success ? logsData.logs.length : '0';
  } catch (e) {
    console.error(e);
    document.getElementById('totalUsers').textContent = 'Error';
    document.getElementById('totalSessions').textContent = 'Error';
  }
}

// -------------------- users list --------------------
async function loadUsers() {
  const usersTableBody = document.getElementById('usersTableBody');
  try {
    const res = await fetch('/api/users', { credentials: 'include' });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();

    if (data.success && data.users) {
      usersTableBody.innerHTML = data.users
        .map(u => {
          const role = (u.role || 'user').toLowerCase();
          const isAdmin = role === 'admin';
          return `
          <tr>
            <td><strong>${u.username || 'Unknown'}</strong></td>
            <td>${u.email || 'No email'}</td>
            <td>
              <span class="badge ${isAdmin ? 'badge-admin' : 'badge-user'}">
                ${role.toUpperCase()}
              </span>
            </td>
            <td>${formatDate(u.created_at)}</td>
            <td>
              <button class="btn btn-sm" onclick="openEditModal('${u._id}')">Edit</button>
              ${
                isAdmin
                  ? '<span class="text-muted" style="margin-left:6px;">Delete disabled</span>'
                  : `<button class="btn btn-danger btn-sm" style="margin-left:6px;" onclick="showDeleteModal('${u._id}','${u.username || 'Unknown'}')">Delete</button>`
              }
            </td>
          </tr>`;
        })
        .join('');
    } else {
      usersTableBody.innerHTML = `<tr><td colspan="5" class="text-center">❌ Error loading users</td></tr>`;
    }
  } catch (e) {
    console.error(e);
    usersTableBody.innerHTML = `<tr><td colspan="5" class="text-center">❌ Connection error</td></tr>`;
  }
}

// -------------------- logs --------------------
async function loadAllLogs() {
  const allLogsContainer = document.getElementById('allLogs');
  try {
    const res = await fetch('/api/stress-logs', { credentials: 'include' });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();

    if (data.success && data.logs && data.logs.length > 0) {
      allLogsContainer.innerHTML = `
        <div class="logs-grid">
          ${data.logs
            .map(
              log => `
            <div class="admin-log-entry">
              <div class="log-header">
                <strong>${log.username || 'Unknown'}</strong>
                <span class="stress-badge ${getStressBadgeClass(log.stress_level)}">
                  ${log.stress_level}%
                </span>
              </div>
              <div class="log-details">
                <div class="log-message">${getStressMessage(log.stress_level)}</div>
                <div class="log-timestamp">${formatDate(log.timestamp)}</div>
              </div>
            </div>`
            )
            .join('')}
        </div>`;
    } else {
      allLogsContainer.innerHTML = `<div class="no-results">📊 No stress detection logs available yet</div>`;
    }
  } catch (e) {
    console.error(e);
    allLogsContainer.innerHTML = `<div class="no-results">❌ Error loading system logs</div>`;
  }
}

// -------------------- delete --------------------
function showDeleteModal(userId, username) {
  userToDelete = userId;
  document.querySelector('#deleteModal p').innerHTML =
    `Are you sure you want to delete user "<strong>${username}</strong>"? This action cannot be undone.`;
  document.getElementById('deleteModal').classList.add('show');
}
function closeDeleteModal() {
  userToDelete = null;
  document.getElementById('deleteModal').classList.remove('show');
}
async function confirmDelete() {
  if (!userToDelete) return;
  try {
    const res = await fetch(`/api/users/${userToDelete}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    const data = await res.json();
    if (data.success) {
      closeDeleteModal();
      loadUsers();
      loadSystemStats();
      showNotification('User deleted successfully', 'success');
    } else {
      showNotification(data.message || 'Failed to delete user', 'error');
    }
  } catch (e) {
    console.error(e);
    showNotification('Connection error while deleting user', 'error');
  }
}

// -------------------- add/edit modal --------------------
function openAddModal() {
  editing = false;
  document.getElementById('userModalTitle').textContent = 'Add User';
  document.getElementById('editingUserId').value = '';
  document.getElementById('usernameInput').value = '';
  document.getElementById('emailInput').value = '';
  document.getElementById('passwordInput').value = '';
  document.getElementById('roleInput').value = 'user';
  document.getElementById('pwdHint').textContent = '(required for new user)';
  document.getElementById('userModal').classList.add('show');
}

async function openEditModal(id) {
  editing = true;
  document.getElementById('userModalTitle').textContent = 'Edit User';
  document.getElementById('pwdHint').textContent = '(leave blank to keep current password)';
  // fetch single user from current table (already loaded)
  // You could also fetch /api/users and filter; we’ll read from table/click:
  const res = await fetch('/api/users', { credentials: 'include' });
  const data = await res.json();
  const u = (data.users || []).find(x => x._id === id);
  if (!u) {
    showNotification('User not found', 'error');
    return;
  }
  document.getElementById('editingUserId').value = id;
  document.getElementById('usernameInput').value = u.username || '';
  document.getElementById('emailInput').value = u.email || '';
  document.getElementById('passwordInput').value = ''; // blank means unchanged
  document.getElementById('roleInput').value = (u.role || 'user').toLowerCase();
  document.getElementById('userModal').classList.add('show');
}

function closeUserModal() {
  document.getElementById('userModal').classList.remove('show');
}

async function submitUserForm(e) {
  e.preventDefault();
  const id = document.getElementById('editingUserId').value;
  const payload = {
    username: document.getElementById('usernameInput').value.trim(),
    email: document.getElementById('emailInput').value.trim() || null,
    role: document.getElementById('roleInput').value
  };
  const pwd = document.getElementById('passwordInput').value;
  if (!editing && !pwd) {
    showNotification('Password is required for new user', 'error');
    return;
  }
  if (pwd) payload.password = pwd;

  try {
    const res = await fetch(id ? `/api/users/${id}` : '/api/users', {
      method: id ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      closeUserModal();
      loadUsers();
      loadSystemStats();
      showNotification(id ? 'User updated' : 'User created', 'success');
    } else {
      showNotification(data.message || 'Operation failed', 'error');
    }
  } catch (err) {
    console.error(err);
    showNotification('Connection error', 'error');
  }
}

// -------------------- helpers --------------------
function getStressBadgeClass(level) {
  if (level < 30) return 'stress-level-0';
  else if (level < 50) return 'stress-level-1';
  else if (level < 70) return 'stress-level-2';
  else return 'stress-level-3';
}

function getStressMessage(level) {
  if (level < 30) return '😊 Low stress detected - Student appears relaxed';
  else if (level < 50) return '😐 Mild stress - Consider short breaks';
  else if (level < 70) return '😰 Moderate stress - Relaxation recommended';
  else return '😟 High stress - Immediate attention needed';
}

function formatDate(dateString) {
  const date = new Date(dateString);
  if (isNaN(date)) return 'Invalid Date';
  return date.toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

function showNotification(message, type) {
  const n = document.createElement('div');
  n.className = `notification ${type}`;
  n.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()">×</button>`;
  document.body.appendChild(n);
  setTimeout(() => n.remove(), 5000);
}

// ---- small styles for new UI bits ----
const adminStyles = `
<style>
  .btn-sm{padding:6px 12px;font-size:.8rem}
  .text-muted{color:#6c757d;font-style:italic}
  .text-center{text-align:center}
  .logs-grid{display:grid;gap:1rem;max-height:500px;overflow-y:auto;padding-right:8px}
  .logs-grid::-webkit-scrollbar{width:6px}
  .logs-grid::-webkit-scrollbar-track{background:#f1f1f1;border-radius:6px}
  .logs-grid::-webkit-scrollbar-thumb{background:#667eea;border-radius:6px}
  .admin-log-entry{background:#f8f9fa;border-radius:8px;padding:1rem;border-left:4px solid #667eea}
  .log-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem}
  .log-details{color:#666}
  .log-message{font-size:.95rem;margin-bottom:.25rem}
  .log-timestamp{font-size:.85rem;color:#888}
  .dashboard-section{display:none;transition:opacity .3s ease}
  .dashboard-section.active{display:block;opacity:1}
  .clickable{cursor:pointer;transition:background-color .3s}
  .clickable:hover{background-color:rgba(0,0,0,.05)}
  .toolbar .btn{border:0;background:#667eea;color:#fff;padding:.6rem 1rem;border-radius:8px;cursor:pointer}
  .modal .form-row{display:flex;flex-direction:column;gap:6px;margin-bottom:10px}
  .modal input,.modal select{padding:.6rem;border:1px solid #ddd;border-radius:8px}
  .notification{position:fixed;top:20px;right:20px;padding:1rem 1.5rem;border-radius:8px;color:#fff;font-weight:500;z-index:1001;display:flex;gap:1rem;animation:slideIn .3s ease}
  .notification.success{background:#28a745}.notification.error{background:#dc3545}
  .notification button{background:none;border:none;color:#fff;font-size:1.2rem;cursor:pointer}
  @keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}
</style>`;
document.head.insertAdjacentHTML('beforeend', adminStyles);
