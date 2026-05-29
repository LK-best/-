/* Cookie bar? */
(function() {
  const accepted = localStorage.getItem('cookiesAccepted');
  const bar = document.getElementById('cookieBar');
  if (accepted && bar) {
    bar.style.display = 'none';
  }

  window.acceptCookies = function() {
    localStorage.setItem('cookiesAccepted', 'true');
    if (bar) bar.style.display = 'none';
  };

  const btn = document.querySelector('.btn-cookie');
  if (btn) {
    btn.addEventListener('click', window.acceptCookies);
  }
})();

/* проверка номера */
(function() {
  const phoneInput = document.getElementById('phone');
  if (!phoneInput) return;

  phoneInput.addEventListener('input', function(e) {
    let val = e.target.value.replace(/\D/g, '');
    if (val.startsWith('7') || val.startsWith('8')) {
      val = val.substring(1);
    }
    let formatted = '+7';
    if (val.length > 0) formatted += ' (' + val.substring(0, 3);
    if (val.length >= 3) formatted += ') ' + val.substring(3, 6);
    if (val.length >= 6) formatted += '-' + val.substring(6, 8);
    if (val.length >= 8) formatted += '-' + val.substring(8, 10);
    e.target.value = formatted;
  });
})();

/* закрыть сообщение по клику */
(function() {
  document.querySelectorAll('.flash').forEach(el => {
    el.addEventListener('click', () => el.remove());
  });
})();
