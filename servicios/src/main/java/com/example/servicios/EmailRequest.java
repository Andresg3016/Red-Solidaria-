package com.example.servicios;

import java.util.List;
import java.util.Map;

public class EmailRequest {
        private String nombreDonador;
        public String getNombreDonador() { return nombreDonador; }
        public void setNombreDonador(String nombreDonador) { this.nombreDonador = nombreDonador; }
    private String destinatario;
    private String nombreFundacion;
    private String estado; 
    
    // --- NUEVOS CAMPOS PARA EL REPORTE ---
    private String nit;
    private int cantidadDonaciones;
    private String categoriaFiltrada;
    private String estadoFiltrado;
    
    // Lista para la tabla del PDF
    private List<Map<String, Object>> donaciones;
        private int fundacionId;

    // Getters y Setters
    public String getDestinatario() { return destinatario; }
    public void setDestinatario(String destinatario) { this.destinatario = destinatario; }
    public String getNombreFundacion() { return nombreFundacion; }
    public void setNombreFundacion(String nombreFundacion) { this.nombreFundacion = nombreFundacion; }
    public String getEstado() { return estado; }
    public void setEstado(String estado) { this.estado = estado; }
    public String getNit() { return nit; }
    public void setNit(String nit) { this.nit = nit; }
    public int getCantidadDonaciones() { return cantidadDonaciones; }
    public void setCantidadDonaciones(int cantidadDonaciones) { this.cantidadDonaciones = cantidadDonaciones; }
    public String getCategoriaFiltrada() { return categoriaFiltrada; }
    public void setCategoriaFiltrada(String categoriaFiltrada) { this.categoriaFiltrada = categoriaFiltrada; }
    public String getEstadoFiltrado() { return estadoFiltrado; }
    public void setEstadoFiltrado(String estadoFiltrado) { this.estadoFiltrado = estadoFiltrado; }
    public List<Map<String, Object>> getDonaciones() { return donaciones; }
    public void setDonaciones(List<Map<String, Object>> donaciones) { this.donaciones = donaciones; }
        public int getFundacionId() { return fundacionId; }
        public void setFundacionId(int fundacionId) { this.fundacionId = fundacionId; }
}