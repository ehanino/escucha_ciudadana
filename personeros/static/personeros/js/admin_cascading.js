(function($) {
    'use strict';

    $(function() {
        console.log("Admin Cascading JS loaded");
        
        // Función principal
        const initCascading = () => {
            const $depto = $('#id_departamento');
            const $prov = $('#id_provincia');
            const $dist = $('#id_distrito');
            const $centro = $('#id_centro_votacion');

            if (!$depto.length) return;

            // --- Cargar Provincias ---
            $depto.on('change', function() {
                const deptoId = $(this).val();
                $prov.empty().append('<option value="">---------</option>');
                $dist.empty().append('<option value="">---------</option>');
                if ($centro.length) $centro.empty().append('<option value="">---------</option>');

                if (!deptoId) return;

                $.getJSON('/personeros/api/provincias/', { departamento: deptoId }, function(data) {
                    $.each(data.provincias, function(index, item) {
                        $prov.append($('<option>', {
                            value: item.id_ubigeo,
                            text: item.nombre
                        }));
                    });
                });
            });

            // --- Cargar Distritos ---
            $prov.on('change', function() {
                const provId = $(this).val();
                $dist.empty().append('<option value="">---------</option>');
                if ($centro.length) $centro.empty().append('<option value="">---------</option>');

                if (!provId) return;

                $.getJSON('/personeros/api/distritos/', { provincia: provId }, function(data) {
                    $.each(data.distritos, function(index, item) {
                        $dist.append($('<option>', {
                            value: item.id_ubigeo,
                            text: item.nombre
                        }));
                    });
                });
            });

            // --- Cargar Centros (si aplica) ---
            if ($centro.length) {
                $dist.on('change', function() {
                    const distId = $(this).val();
                    $centro.empty().append('<option value="">---------</option>');

                    if (!distId) return;

                    $.getJSON('/personeros/api/centros/', { distrito: distId }, function(data) {
                        $.each(data.centros, function(index, item) {
                            $centro.append($('<option>', {
                                value: item.id,
                                text: item.nombre
                            }));
                        });
                    });
                });
            }
        };

        initCascading();
    });
})(django.jQuery || jQuery || $);
