/* Funciones que comparten los buscadores de Memorias y de Vestigio */
window.Buscador = (function () {

    // Minúsculas y sin tildes (también la ñ): "Güegüense" y "gueguense" se encuentran entre sí
    function normalizar(texto) {
        return String(texto || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    // Todas las palabras que se escribieron tienen que aparecer en el texto, en cualquier orden
    function coincide(textoNormalizado, consulta) {
        return normalizar(consulta).split(/\s+/).filter(Boolean).every(function (palabra) {
            return textoNormalizado.indexOf(palabra) !== -1;
        });
    }

    // Desde qué fecha (AAAA-MM-DD) cuenta cada periodo; vacío = cualquier fecha
    function desde(periodo) {
        const dias = { semana: 7, mes: 30, anio: 365 }[periodo];
        if (!dias) return '';
        const f = new Date();
        f.setDate(f.getDate() - dias);
        return f.getFullYear() + '-' + String(f.getMonth() + 1).padStart(2, '0') + '-' + String(f.getDate()).padStart(2, '0');
    }

    function cumpleFecha(fecha, periodo) {
        const minima = desde(periodo);
        return !minima || (fecha !== undefined && fecha !== '' && fecha >= minima);
    }

    // Ordena una lista de elementos (que traen data-fecha) por fecha o por título; devuelve una lista nueva
    function ordenar(elementos, orden, titulo) {
        return elementos.slice().sort(function (a, b) {
            const comparar = function () { return titulo(a).localeCompare(titulo(b), 'es', { sensitivity: 'base' }); };
            if (orden === 'nombre') return comparar();
            const fa = a.dataset.fecha || '';
            const fb = b.dataset.fecha || '';
            if (fa !== fb) return orden === 'antiguos' ? (fa < fb ? -1 : 1) : (fa < fb ? 1 : -1);
            return comparar();
        });
    }

    // El botón de filtros muestra y oculta el panel con las opciones; la insignia cuenta los filtros activos.
    // Esc cierra el panel y devuelve el foco al botón. Devuelve una función para actualizar el numerito.
    function panelDeFiltros(boton, panel, insignia) {
        function mostrar(abrir) {
            panel.hidden = !abrir;
            boton.setAttribute('aria-expanded', abrir ? 'true' : 'false');
        }
        boton.addEventListener('click', function () { mostrar(panel.hidden); });
        boton.closest('form').addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !panel.hidden) { mostrar(false); boton.focus(); }
        });
        return function (activos) {
            insignia.textContent = activos;
            insignia.hidden = activos === 0;
            boton.setAttribute('aria-label', activos ? 'Filtros (' + activos + (activos === 1 ? ' activo)' : ' activos)') : 'Filtros');
        };
    }

    return { normalizar: normalizar, coincide: coincide, cumpleFecha: cumpleFecha, ordenar: ordenar, panelDeFiltros: panelDeFiltros };
})();