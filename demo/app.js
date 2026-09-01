const text = document.querySelector('#text');
const preview = document.querySelector('#preview');
const stage = document.querySelector('#stage');
const size = document.querySelector('#size');
const spacing = document.querySelector('#spacing');
const leading = document.querySelector('#leading');
const update = () => {
  preview.textContent = text.value || 'TYPE SOMETHING';
  preview.style.fontSize = `${size.value}px`;
  preview.style.letterSpacing = `${spacing.value}px`;
  preview.style.lineHeight = leading.value;
  document.querySelector('#sizeValue').textContent = `${size.value}px`;
  document.querySelector('#spacingValue').textContent = `${spacing.value}px`;
  document.querySelector('#leadingValue').textContent = leading.value;
};
[text, size, spacing, leading].forEach(control => control.addEventListener('input', update));
document.querySelector('#copy').addEventListener('click', async (event) => {
  await navigator.clipboard.writeText(text.value);
  event.currentTarget.textContent = 'Copied';
  setTimeout(() => event.currentTarget.textContent = 'Copy text', 1200);
});
update();
