<?php
require_once 'config.php';

$token = $_GET['t'] ?? null;
if (!$token) die("Acceso denegado.");

// 1. Buscamos la transacción por el token
$stmt = $pdo->prepare("SELECT * FROM transacciones_monetarias WHERE token_cajita = ?");
$stmt->execute([$token]);
$data = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$data) die("Cajita no encontrada.");

// 2. Máscara de tarjeta (Simple y directo)
$tarjeta = "****-****-****-" . substr($data['tarjeta_encriptada'], -4);
?>

<div class="cajita-sorpresa" style="border: 2px solid #43c98a; padding: 20px; border-radius: 15px;">
    <h2>🎁 ¡Gracias por tu donación!</h2>
    <h2>Detalles de tu Cajita Sorpresa:Tu generosidad ha ayudado a cambiar vidas. ❤️</h2>
    <p><strong>Fundación:</strong> <?php echo htmlspecialchars($data['fundacion_nombre']); ?></p>
    <p><strong>NIT:</strong> <?php echo htmlspecialchars($data['fundacion_nit']); ?></p>
    <p><strong>Monto:</strong> $<?php echo number_format($data['monto'], 2); ?></p>
    <p><strong>Tarjeta:</strong> <?php echo $tarjeta; ?></p>
    
    <a href="generar_pdf.php?id=<?php echo $data['id']; ?>" class="btn-pdf">📥 Descargar Recibo PDF</a>
</div>