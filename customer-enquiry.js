// UGGI-RAY Customer Enquiry V1
// Replace WHATSAPP_NUMBER with the business WhatsApp number before publishing.
// Keep the number in international format without +, spaces, or brackets.
const WHATSAPP_NUMBER = "YOUR_WHATSAPP_NUMBER";

const $ = id => document.getElementById(id);
$("send").addEventListener("click", () => {
  const service = $("service").value;
  const name = $("name").value.trim() || "Customer";
  const details = $("details").value.trim() || "I would like more information.";
  if (WHATSAPP_NUMBER === "YOUR_WHATSAPP_NUMBER") {
    $("status").textContent = "WhatsApp destination still needs to be configured.";
    return;
  }
  const text = `Hello UGGI-RAY, my name is ${name}. I am interested in: ${service}. ${details}`;
  window.location.href = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(text)}`;
});
