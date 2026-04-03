package com.example.servicios;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/email")
public class EmailController {

    @Autowired
    private EmailService emailService;

    @PostMapping("/enviar")
    public String enviarEmail(@RequestBody EmailRequest request) {
        try {
            emailService.enviarNotificacion(request);
            return "{\"status\": \"Enviado correctamente\"}";
        } catch (Exception e) {
            return "{\"status\": \"Error\", \"error\": \"" + e.getMessage() + "\"}";
        }
    }
}
