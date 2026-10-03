<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor DP - Zona Centro</title>
    <!-- Tailwind CSS para los estilos visuales -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- SheetJS para procesar el Excel localmente sin Python -->
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    <!-- Chart.js para las gráficas -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-slate-50 font-sans p-4 md:p-6 text-slate-800">

    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Encabezado -->
        <header class="bg-white rounded-2xl shadow-sm p-6 border-t-4 border-blue-600 flex flex-col md:flex-row justify-between items-center">
            <div>
                <h1 class="text-2xl font-black text-slate-800 flex items-center space-x-2">
                    <span class="text-3xl">⚡</span> 
                    <span>Monitor de Daños Pendientes (DP) - Zona Centro</span>
                </h1>
                <p class="text-slate-500 text-sm font-medium mt-1">Visualización de tiempos de atención (SLA: Urbano = 1 día | Rural = 3 días)</p>
            </div>
            <div class="mt-4 md:mt-0">
                <label class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-6 rounded-xl cursor-pointer shadow-md transition inline-flex items-center space-x-2 text-sm">
                    <span>📂 Actualizar reporte del día (Excel)</span>
                    <input type="file" id="fileUpload" class="hidden" accept=".xlsx, .xls, .csv">
                </label>
            </div>
        </header>

        <!-- Contenedor del Dashboard (Oculto inicialmente) -->
        <div id="dashboard" class="hidden space-y-6">
            
            <!-- Tarjetas de Métricas -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white rounded-2xl shadow-sm border border-red-200 p-6 flex items-center justify-between border-l-4 border-l-red-500">
                    <div>
                        <p class="text-xs font-bold text-red-500 uppercase tracking-wider">🔴 Vencidos</p>
                        <h3 id="countVencido" class="text-4xl font-black text-slate-800 mt-2">0</h3>
                    </div>
                </div>
                <div class="bg-white rounded-2xl shadow-sm border border-amber-200 p-6 flex items-center justify-between border-l-4 border-l-amber-500">
                    <div>
                        <p class="text-xs font-bold text-amber-500 uppercase tracking-wider">🟡 Al Límite</p>
                        <h3 id="countLimite" class="text-4xl font-black text-slate-800 mt-2">0</h3>
                    </div>
                </div>
                <div class="bg-white rounded-2xl shadow-sm border border-emerald-200 p-6 flex items-center justify-between border-l-4 border-l-emerald-500">
                    <div>
                        <p class="text-xs font-bold text-emerald-500 uppercase tracking-wider">🟢 A Tiempo</p>
                        <h3 id="countTiempo" class="text-4xl font-black text-slate-800 mt-2">0</h3>
                    </div>
                </div>
            </div>

            <!-- Gráficas -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Gráfica Circular -->
                <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wide mb-4">Distribución General SLA</h3>
                    <div class="relative h-64 flex justify-center">
                        <canvas id="pieChart"></canvas>
                    </div>
                </div>
                <!-- Gráfica de Barras -->
                <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wide mb-4">Top 10 DP Críticos con más días</h3>
                    <div class="relative h-64">
                        <canvas id="barChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Tabla de Datos -->
            <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <div class="p-5 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
                    <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wide">Detalle Operativo para Despacho</h3>
                    <span id="totalRegistros" class="text-xs font-bold text-slate-500">0 Registros</span>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-left text-xs border-collapse">
                        <thead class="bg-slate-100 text-slate-500 sticky top-0">
                            <tr>
                                <th class="p-3">Identificación</th>
                                <th class="p-3">Subestación</th>
                                <th class="p-3">Instrucción</th>
                                <th class="p-3">Dirección del dispositivo</th>
                                <th class="p-3">Tipo de Sector</th>
                                <th class="p-3 text-center">Días Sin Servicio</th>
                                <th class="p-3 text-center">Estado SLA</th>
                                <th class="p-3">Cuadrillas</th>
                            </tr>
                        </thead>
                        <tbody id="tableBody" class="divide-y divide-slate-100">
                            <!-- Filas inyectadas por JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Pantalla de inicio -->
        <div id="welcomeState" class="bg-white rounded-2xl shadow-sm p-16 text-center border border-slate-200 mt-6">
            <div class="text-6xl mb-4">📊</div>
            <h2 class="text-xl font-bold text-slate-800 mb-2">Carga el reporte de Excel para monitorear los DP</h2>
            <p class="text-slate-500 text-sm max-w-lg mx-auto">El sistema detectará automáticamente las direcciones para clasificarlas en RURAL o URBANO y aplicará la regla de SLA correspondiente sin necesidad de servidor.</p>
        </div>

    </div>

    <script>
        let globalData = [];
        let pieChartInst = null;
        let barChartInst = null;

        // Paleta de colores requerida
        const COLORS = {
            'A Tiempo': '#10b981', // Emerald 500
            'Al Límite': '#f59e0b', // Amber 500
            'Vencido': '#ef4444'    // Red 500
        };
        const BG_COLORS = {
            'A Tiempo': 'bg-emerald-50 text-emerald-700',
            'Al Límite': 'bg-amber-50 text-amber-700',
            'Vencido': 'bg-red-50 text-red-700 font-bold'
        };

        document.getElementById('fileUpload').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                const data = new Uint8Array(e.target.result);
                // cellDates: true asegura que leamos la fecha correctamente
                const workbook = XLSX.read(data, {type: 'array', cellDates: true});
                const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                
                // Convertir a array (filas x columnas) para detectar inteligentemente la cabecera
                const rows = XLSX.utils.sheet_to_json(firstSheet, {header: 1});
                procesarExcel(rows);
            };
            reader.readAsArrayBuffer(file);
        });

        function procesarExcel(rows) {
            // 1. Detección automática del encabezado (No depende del "header=5" fijo)
            let headerIdx = -1;
            for (let i = 0; i < Math.min(15, rows.length); i++) {
                let rowStr = rows[i].map(c => String(c).toLowerCase());
                // Si encontramos columnas clave, esa es la fila de encabezados
                if (rowStr.some(c => c.includes('identificaci') || c.includes('instrucci'))) {
                    headerIdx = i;
                    break;
                }
            }

            if (headerIdx === -1) {
                alert("No se encontró la cabecera de datos en el archivo. Verifica el formato.");
                return;
            }

            // 2. Extraer datos estructurados
            let headers = rows[headerIdx].map(h => String(h).trim().toLowerCase());
            let dataRows = rows.slice(headerIdx + 1);

            // Índices de columnas
            let idxId = headers.findIndex(h => h.includes('identificaci'));
            let idxSub = headers.findIndex(h => h.includes('subestaci'));
            let idxInst = headers.findIndex(h => h.includes('instrucci'));
            let idxDir = headers.findIndex(h => h.includes('direcci'));
            let idxFecha = headers.findIndex(h => h.includes('fecha de creaci'));
            let idxCuad = headers.findIndex(h => h.includes('cuadrillas'));

            let hoy = new Date();
            hoy.setHours(0,0,0,0); // Normalizar a medianoche para cálculo exacto de días

            globalData = [];

            dataRows.forEach(row => {
                let identificacion = idxId !== -1 ? row[idxId] : null;
                if (!identificacion) return; // Omitir filas vacías

                let direccion = idxDir !== -1 ? String(row[idxDir] || '') : '';
                let subestacion = idxSub !== -1 ? String(row[idxSub] || '') : '';
                let instruccion = idxInst !== -1 ? String(row[idxInst] || '') : '';
                let cuadrillas = idxCuad !== -1 ? String(row[idxCuad] || '') : '';
                let fechaCreacionRaw = idxFecha !== -1 ? row[idxFecha] : null;

                // CLASIFICAR SECTOR (URBANO / RURAL)
                let tipoSector = 'URBANO';
                let dirUpper = direccion.toUpperCase();
                let rurales = ['VDA', 'VEREDA', 'FCA', 'FINCA', 'CORREGIMIENTO'];
                if (rurales.some(kw => dirUpper.includes(kw))) {
                    tipoSector = 'RURAL';
                }

                // CALCULAR DÍAS SIN SERVICIO
                let diasSinServicio = 0;
                let fechaStr = "N/A";
                if (fechaCreacionRaw) {
                    let fechaCalculo = new Date(fechaCreacionRaw);
                    if (!isNaN(fechaCalculo.getTime())) {
                        fechaCalculo.setHours(0,0,0,0);
                        let diffTime = hoy - fechaCalculo;
                        diasSinServicio = Math.max(0, Math.floor(diffTime / (1000 * 60 * 60 * 24)));
                        fechaStr = `${fechaCalculo.getDate().toString().padStart(2,'0')}/${(fechaCalculo.getMonth()+1).toString().padStart(2,'0')}/${fechaCalculo.getFullYear()}`;
                    }
                }

                // EVALUACIÓN SLA
                let limite = tipoSector === 'RURAL' ? 3 : 1;
                let estadoSLA = 'A Tiempo';
                if (diasSinServicio > limite) {
                    estadoSLA = 'Vencido';
                } else if (diasSinServicio === limite) {
                    estadoSLA = 'Al Límite';
                }

                globalData.push({
                    identificacion, subestacion, instruccion, direccion, 
                    tipoSector, diasSinServicio, estadoSLA, cuadrillas, fechaStr
                });
            });

            actualizarDashboard();
        }

        function actualizarDashboard() {
            document.getElementById('welcomeState').classList.add('hidden');
            document.getElementById('dashboard').classList.remove('hidden');

            // Actualizar Tarjetas KPI
            let vencidos = globalData.filter(d => d.estadoSLA === 'Vencido').length;
            let limite = globalData.filter(d => d.estadoSLA === 'Al Límite').length;
            let aTiempo = globalData.filter(d => d.estadoSLA === 'A Tiempo').length;

            document.getElementById('countVencido').innerText = vencidos;
            document.getElementById('countLimite').innerText = limite;
            document.getElementById('countTiempo').innerText = aTiempo;
            document.getElementById('totalRegistros').innerText = `${globalData.length} Registros procesados`;

            dibujarGraficas(vencidos, limite, aTiempo);
            dibujarTabla();
        }

        function dibujarGraficas(vencidos, limite, aTiempo) {
            // 1. Gráfica Circular (Pie)
            if (pieChartInst) pieChartInst.destroy();
            const ctxPie = document.getElementById('pieChart').getContext('2d');
            pieChartInst = new Chart(ctxPie, {
                type: 'pie',
                data: {
                    labels: ['Vencidos', 'Al Límite', 'A Tiempo'],
                    datasets: [{
                        data: [vencidos, limite, aTiempo],
                        backgroundColor: [COLORS['Vencido'], COLORS['Al Límite'], COLORS['A Tiempo']]
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // 2. Gráfica de Barras Horizontal (Top 10 Críticos)
            let top10 = [...globalData].sort((a, b) => b.diasSinServicio - a.diasSinServicio).slice(0, 10);
            
            if (barChartInst) barChartInst.destroy();
            const ctxBar = document.getElementById('barChart').getContext('2d');
            barChartInst = new Chart(ctxBar, {
                type: 'bar',
                data: {
                    labels: top10.map(d => d.identificacion),
                    datasets: [{
                        label: 'Días Sin Servicio',
                        data: top10.map(d => d.diasSinServicio),
                        backgroundColor: top10.map(d => COLORS[d.estadoSLA])
                    }]
                },
                options: {
                    indexAxis: 'y', // Barra horizontal
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { beginAtZero: true, title: { display: true, text: 'Días Transcurridos' } }
                    }
                }
            });
        }

        function dibujarTabla() {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            // Ordenar: primero vencidos, luego por cantidad de días
            let sortedData = [...globalData].sort((a, b) => {
                const ordenSLA = {'Vencido': 1, 'Al Límite': 2, 'A Tiempo': 3};
                if (ordenSLA[a.estadoSLA] !== ordenSLA[b.estadoSLA]) {
                    return ordenSLA[a.estadoSLA] - ordenSLA[b.estadoSLA];
                }
                return b.diasSinServicio - a.diasSinServicio;
            });

            sortedData.forEach(row => {
                let badgeClass = row.estadoSLA === 'Vencido' ? 'bg-red-500 text-white' : 
                                 row.estadoSLA === 'Al Límite' ? 'bg-amber-500 text-white' : 'bg-emerald-500 text-white';
                                 
                tbody.innerHTML += `
                    <tr class="${BG_COLORS[row.estadoSLA]} border-b border-slate-100 hover:opacity-80 transition">
                        <td class="p-3 font-bold">${row.identificacion}</td>
                        <td class="p-3 font-medium">${row.subestacion}</td>
                        <td class="p-3">${row.instruccion}</td>
                        <td class="p-3 text-slate-600 truncate max-w-xs" title="${row.direccion}">${row.direccion}</td>
                        <td class="p-3 font-bold">${row.tipoSector}</td>
                        <td class="p-3 text-center text-base">${row.diasSinServicio}</td>
                        <td class="p-3 text-center">
                            <span class="px-2 py-1 rounded shadow-sm text-xs font-bold ${badgeClass}">${row.estadoSLA}</span>
                        </td>
                        <td class="p-3 truncate max-w-[120px] text-xs" title="${row.cuadrillas}">${row.cuadrillas}</td>
                    </tr>
                `;
            });
        }
    </script>
</body>
</html>
