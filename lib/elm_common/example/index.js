var app = Elm.Main.fullscreen();

console.log('Run App', app);
window.localstorage(app, 'bugzilla');
window.localstorage(app, 'taskclusterlogin');
window.redirect(app);
