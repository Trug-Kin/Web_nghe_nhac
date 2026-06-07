// Lấy JWT token từ cookies - GLOBAL FUNCTION
(function() {
  'use strict';
  
  function getJwtToken() {
    const cookies = document.cookie;
    const token = cookies
      .split("; ")
      .find((row) => row.startsWith("access_token="));
    
    return token ? token.split("=")[1] : null;
  }

  // Export globally
  window.getJwtToken = getJwtToken;

  // BACKWARD COMPATIBILITY: Override localStorage.getItem for 'access_token' (only once)
  if (!window._jwtStorageOverridden) {
    const originalGetItem = Storage.prototype.getItem;
    Storage.prototype.getItem = function(key) {
      if (key === 'access_token') {
        // Silently redirect to cookie instead of localStorage
        return getJwtToken();
      }
      return originalGetItem.call(this, key);
    };
    window._jwtStorageOverridden = true;
  }

  document.addEventListener("DOMContentLoaded", function () {
    // checkLoginStatus handled by loginbutton.js
    // Removed duplicate call to avoid undefined function errors
  });

  // Kiểm tra trạng thái đăng nhập - DISABLED, handled by loginbutton.js
  // function checkLoginStatus() {
  //   const token = getJwtToken();
  //   if (token) {
  //     setLoggedInUI();
  //   } else {
  //     resetUI();
  //   }
  // }
})();