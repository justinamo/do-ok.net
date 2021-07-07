var dragged;
var activeTags = [];

document.addEventListener("drag", function(event) {}, false);

document.addEventListener("dragstart", function(event) {
  dragged = event.target;
}, false);

/* events fired on the drop targets */
document.addEventListener("dragover", function(event) {
  event.preventDefault();
}, false);

document.addEventListener("dragenter", function(event) {
  if (event.target.classList && event.target.classList.contains("dropzone")) {
    event.target.style.background = "#ddd";
  }
}, false);

document.addEventListener("dragleave", function(event) {
  if (event.target.classList && event.target.classList.contains("dropzone")) {
    event.target.style.background = "";
  }
}, false);

document.addEventListener("drop", function(event) {
  event.preventDefault();
  if (event.target.classList && event.target.classList.contains("dropzone")) {
    event.target.style.background = "";
    dragged.parentNode.removeChild(dragged);
    event.target.appendChild(dragged);

    emptyActiveTags();
    fillActiveTags();
    console.log("activetags: ", activeTags);

    if (event.target.id === "activetags" || event.target.id === "othertags") {
      window.location.search = "tags=" + activeTags.join(',');
    }
  }
}, false);

function emptyActiveTags() {
  while (activeTags.length > 0) {
    activeTags.pop();
  };
}

function fillActiveTags(live) {
  var nodes = document.getElementById("activetags").children;
  for (var i = 0; i < nodes.length; i++) {
    activeTags.push(extractTagName(nodes[i])); 
  };
}

function extractTagName(tagNode) {
  return tagNode.text.trim().slice(1); 
}

function replaceContent() {};

