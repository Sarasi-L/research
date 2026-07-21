//frontend/js/landing.js

const cvs = document.getElementById('cvs');
const ctx = cvs.getContext('2d');

function rs(){ cvs.width = innerWidth; cvs.height = innerHeight; }
rs(); addEventListener('resize', rs);

const pts = Array.from({length:52}, () => ({
    x: Math.random() * innerWidth * .5,
    y: Math.random() * innerHeight,
    r: Math.random() * 1.3 + .2,
    dx: (Math.random() - .5) * .28,
    dy: (Math.random() - .5) * .28,
    a: Math.random() * .5 + .08
}));

(function tick(){
    ctx.clearRect(0, 0, cvs.width, cvs.height);

    const g = ctx.createRadialGradient(cvs.width*.22, cvs.height*.55, 0, cvs.width*.22, cvs.height*.55, cvs.width*.38);
    g.addColorStop(0, 'rgba(0,150,255,0.055)');
    g.addColorStop(1, 'transparent');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cvs.width, cvs.height);

    pts.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
        ctx.fillStyle = `rgba(0,150,255,${p.a})`;
        ctx.fill();
        p.x += p.dx; p.y += p.dy;
        if (p.x < 0 || p.x > cvs.width*.5) p.dx *= -1;
        if (p.y < 0 || p.y > cvs.height) p.dy *= -1;
    });

    for (let i = 0; i < pts.length; i++) {
        for (let j = i+1; j < pts.length; j++) {
            const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
            if (d < 88) {
                ctx.beginPath();
                ctx.strokeStyle = `rgba(0,150,255,${.065*(1-d/88)})`;
                ctx.lineWidth = .5;
                ctx.moveTo(pts[i].x, pts[i].y);
                ctx.lineTo(pts[j].x, pts[j].y);
                ctx.stroke();
            }
        }
    }
    requestAnimationFrame(tick);
})();

function go() {
    document.body.style.transition = 'opacity .4s ease';
    document.body.style.opacity = '0';
    setTimeout(() => { window.location.href = 'index.html'; }, 400);
}