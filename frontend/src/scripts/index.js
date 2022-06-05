import "../styles/index.scss";
import 'bootstrap';
import "bootstrap-show-password/dist/bootstrap-show-password.js";
import "htmx.org";

function importAll(r) {
    return r.keys().map(r);
}

const images = importAll(require.context('../img', false, /\.(png|jpe?g|svg)$/));