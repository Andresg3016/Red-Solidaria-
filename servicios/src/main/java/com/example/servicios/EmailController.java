package com.example.servicios;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/email")
public class EmailController {

    @Autowired
    private EmailService emailService;

    // 1. Endpoint original para notificaciones de cuenta (PENDIENTE/APROBADO)
    @PostMapping("/enviar")
    public String enviarEmail(@RequestBody EmailRequest request) {
        try {
            emailService.enviarNotificacion(request);
            return "{\"status\": \"Notificación enviada\"}";
        } catch (Exception e) {
            return "{\"status\": \"Error\", \"error\": \"" + e.getMessage() + "\"}";
        }
    }

    // 2. NUEVO: Endpoint específico para el Reporte Multicriterio
    @PostMapping("/enviar-reporte")
    public String enviarReporte(@RequestBody EmailRequest request) {
        try {
            // Llamamos al nuevo método que crearemos en el servicio
            emailService.enviarReporteEmail(request); 
            return "{\"status\": \"Reporte enviado\"}";
        } catch (Exception e) {
            return "{\"status\": \"Error\", \"error\": \"" + e.getMessage() + "\"}";
        }
    }
}