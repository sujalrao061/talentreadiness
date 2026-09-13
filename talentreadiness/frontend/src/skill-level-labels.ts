const skillLevels = ['Beginner', 'Basic', 'Intermediate', 'Advanced', 'Expert'];

function replaceNumericSkillLevels() {
  document.querySelectorAll<HTMLSelectElement>('select[name="level"]').forEach((select) => {
    [...select.options].forEach((option, index) => {
      const label = skillLevels[index];
      if (label && option.textContent !== label) option.textContent = label;
    });
  });
}

new MutationObserver(replaceNumericSkillLevels).observe(document.documentElement, {
  childList: true,
  subtree: true,
});
replaceNumericSkillLevels();
const notificationStyle = document.createElement('style');
notificationStyle.textContent = '.employee-alert{position:relative}.employee-alert i{position:absolute;top:-5px;right:-5px;width:9px;height:9px;border-radius:50%;background:#f97316;color:transparent;font-size:0}.public-nav:after{content:"Build Resilient Teams";position:fixed;right:7vw;top:33px;color:#f8fafc;font:700 13px Arial;letter-spacing:.1em;text-transform:uppercase}';
document.head.appendChild(notificationStyle);
const successNoticeStyle = document.createElement('style');
successNoticeStyle.textContent = '.notice{display:block!important;border:1px solid #22c55e!important;background:#ecfdf5!important;color:#065f46!important;font-weight:700!important}';
document.head.appendChild(successNoticeStyle);
setTimeout(() => document.head.appendChild(successNoticeStyle.cloneNode(true)), 50);

function addWorkIdField() {
  if (location.pathname !== '/signup') return;
  const form = document.querySelector('.auth form');
  if (!form || form.querySelector('[name="work_id"]')) return;
  const label = document.createElement('label');
  label.textContent = 'Work ID';
  label.innerHTML += '<input name="work_id" placeholder="MGR-1001 or EMP-1001" required />';
  form.querySelector('label:nth-of-type(2)')?.before(label);
  const phone = document.createElement('label');
  phone.textContent = 'Phone number (demo verification)';
  phone.innerHTML += '<div style="display:flex;gap:8px"><input name="phone" type="tel" placeholder="555-0100" required /><button type="button" id="send-demo-otp">Send OTP</button></div>';
  label.after(phone);
  const otp = document.createElement('label');
  otp.textContent = 'Verification code';
  otp.innerHTML += '<input name="otp" inputmode="numeric" placeholder="Enter OTP" /><small>Demo code: 123456</small>';
  phone.after(otp);
  otp.querySelector('#send-demo-otp')?.addEventListener('click', () => alert('Demo OTP sent: 123456'));
}
new MutationObserver(addWorkIdField).observe(document.documentElement, { childList: true, subtree: true });
addWorkIdField();
document.addEventListener('submit', async (event) => {
  const form = event.target as HTMLFormElement;
  if (location.pathname !== '/signup' || !form.matches('.auth form')) return;
  event.preventDefault(); event.stopImmediatePropagation();
  const data = new FormData(form);
  const response = await fetch('http://127.0.0.1:8000/auth/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: data.get('name'), email: data.get('email'), password: data.get('password'), work_id: data.get('work_id') }) });
  if (!response.ok) { const error = await response.json(); return alert(typeof error.detail === 'string' ? error.detail : 'Check your details. Work ID must start with MGR- or EMP-.'); }
  const result = await response.json(); localStorage.setItem('tr-token', result.access_token); localStorage.setItem('tr-user', JSON.stringify(result.user)); location.assign(result.user.role === 'manager' ? '/manager/dashboard' : '/employee/dashboard');
}, true);
