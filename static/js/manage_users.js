// Quản lý user cho admin (SPA, fetch API, debug rõ ràng)
(function() {
  function getTableBody(){
    return document.getElementById('users-table')?.querySelector('tbody');
  }

  function showError(msg){
    const table = getTableBody();
    if(!table) return;
    table.innerHTML = `<tr><td colspan='5' class='error-message'>${msg}</td></tr>`;
  }
  function showLoading(){
    const table = getTableBody();
    if(!table) return;
    table.innerHTML = `<tr><td colspan='5' class='loading-message'>Đang tải dữ liệu...</td></tr>`;
  }

  async function loadUsers() {
    const table = getTableBody();
    if(!table) return; // not on users page yet
    showLoading();
    try {
  const token = document.cookie.split('; ').find(row => row.startsWith('access_token='));
      const headers = {'Content-Type':'application/json'};
      if(token) headers['Authorization'] = 'Bearer ' + token.split('=')[1];
      const res = await fetch('/admin/api/users', {headers, credentials:'include'});
      if(res.status === 403) {
        showError('Bạn không có quyền truy cập trang này');
        return;
      }
      if(!res.ok) {
        showError('Lỗi kết nối server');
        return;
      }
      let users = await res.json();
      if(!Array.isArray(users)) {
        showError('Lỗi dữ liệu từ server');
        return;
      }
      if(users.length === 0) {
        table.innerHTML = `<tr><td colspan='5' style='text-align:center;padding:40px;color:#b3b3b3;'>Chưa có người dùng nào</td></tr>`;
        return;
      }
  renderTable(users);
      // Tìm kiếm username
      const searchInput = document.getElementById('search-username-input');
      if(searchInput) {
        searchInput.addEventListener('input', function() {
          const keyword = this.value.trim().toLowerCase();
          const filtered = users.filter(u => u.username.toLowerCase().includes(keyword));
          renderTable(filtered);
        });
      }
    } catch(e) {
      showError('Lỗi kết nối server');
    }
  }

  function renderTable(userList) {
    const table = getTableBody();
    if(!table) return;
    table.innerHTML = '';
    userList.forEach((u, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${idx+1}</td>
        <td>${u.username}</td>
        <td>${u.email}</td>
        <td>
          <select class="role-select" data-user-id="${u.id}" data-current-role="${u.role}">
            <option value="admin" ${u.role==='admin'?'selected':''}>Admin</option>
            <option value="uploader" ${u.role==='uploader'?'selected':''}>Uploader</option>
            <option value="user" ${u.role==='user'?'selected':''}>User</option>
          </select>
        </td>
        <td>
          <div class="action-buttons">
            <button class="set-role-btn" data-user-id="${u.id}">Set Role</button>
            <button class="delete-user-btn" data-user-id="${u.id}">Xóa</button>
          </div>
        </td>
      `;
      table.appendChild(tr);
    });
    // Gắn lại sự kiện cho nút sau khi render
  table.querySelectorAll('.set-role-btn').forEach(btn => {
      btn.addEventListener('click', async function(){
        const userId = this.getAttribute('data-user-id');
  const tableNow = getTableBody();
  const select = tableNow?.querySelector(`.role-select[data-user-id="${userId}"]`);
        const newRole = select.value;
        const currentRole = select.getAttribute('data-current-role');
        if(newRole === currentRole) return;
        btn.disabled = true;
        try {
          const token = document.cookie.split('; ').find(row => row.startsWith('access_token='));
          const headers = {'Content-Type':'application/json'};
          if(token) headers['Authorization'] = 'Bearer ' + token.split('=')[1];
          const res = await fetch(`/admin/api/users/${userId}/role`, {
            method: 'POST',
            headers,
            body: JSON.stringify({role: newRole})
          });
          if(!res.ok) throw new Error('Lỗi server');
          const apiResult = await res.json();
          console.log('Set role response:', apiResult);
          // Reload user list to reflect updated role
          await loadUsers();
          btn.textContent = '✔';
          btn.style.background = '#1db954';
          setTimeout(() => {
            btn.textContent = 'Set Role';
            btn.style.background = '#1db954';
            btn.disabled = false;
          }, 1500);
        } catch(e) {
          btn.textContent = 'Lỗi';
          btn.style.background = '#ff4444';
          setTimeout(() => {
            btn.textContent = 'Set Role';
            btn.style.background = '#1db954';
            btn.disabled = false;
          }, 1500);
        }
      });
    });
  table.querySelectorAll('.delete-user-btn').forEach(btn => {
      btn.addEventListener('click', async function(){
        if(!confirm('Bạn có chắc muốn xóa user này?')) return;
        btn.disabled = true;
        try {
          const token = document.cookie.split('; ').find(row => row.startsWith('access_token='));
          const headers = {'Content-Type':'application/json'};
          if(token) headers['Authorization'] = 'Bearer ' + token.split('=')[1];
          const res = await fetch(`/admin/api/users/${btn.getAttribute('data-user-id')}`, {
            method: 'DELETE',
            headers
          });
          if(!res.ok) throw new Error('Lỗi server');
          btn.closest('tr').remove();
        } catch(e) {
          btn.textContent = 'Lỗi';
          setTimeout(()=>btn.textContent='Xóa', 1200);
        } finally {
          btn.disabled = false;
        }
      });
    });
  }

  // Initial direct load (if already on page)
  if(window.location.pathname === '/admin/users') loadUsers();
  // Khi chuyển trang SPA
  window.addEventListener('spa-navigated', loadUsers);

})();
