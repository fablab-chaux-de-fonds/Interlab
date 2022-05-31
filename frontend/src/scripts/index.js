import "../styles/index.scss";
import 'bootstrap';
import "bootstrap-show-password/dist/bootstrap-show-password.js";
import "htmx.org";

window.bootstrap = require('bootstrap/dist/js/bootstrap.bundle.min.js');

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl);
});

function importAll(r) {
    return r.keys().map(r);
}

const images = importAll(require.context('../img', false, /\.(png|jpe?g|svg)$/));