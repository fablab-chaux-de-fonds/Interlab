//require('bootstrap-icons/font/bootstrap-icons.css');
import "../styles/index.scss";
import "bootstrap/dist/js/bootstrap.bundle";
import "htmx.org";

function importAll(r) {
    return r.keys().map(r);
  }
  
const images = importAll(require.context('../img', false, /\.(png|jpe?g|svg)$/));