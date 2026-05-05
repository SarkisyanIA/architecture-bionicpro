package com.example.reportservice.controller;

import com.example.reportservice.model.ReportResponse;
import com.example.reportservice.service.ReportService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/reports")
@RequiredArgsConstructor
@CrossOrigin(origins = "http://localhost:3000")
public class ReportController {

    private final ReportService reportService;

    @GetMapping("/{customerId}")
    public ResponseEntity<ReportResponse> getReport(
            @PathVariable String customerId,
            @AuthenticationPrincipal Jwt jwt) {

        // Получаем ID пользователя из JWT токена
        String userIdFromToken = extractUserIdFromToken(jwt);

        log.info("User {} requesting report for customer {}", userIdFromToken, customerId);

        // Проверяем, что пользователь запрашивает свой собственный отчёт
        if (!userIdFromToken.equals(customerId)) {
            log.warn("User {} attempted to access report of user {}", userIdFromToken, customerId);
            return ResponseEntity.status(403).build();
        }

        ReportResponse report = reportService.getCustomerReport(customerId);

        if (report == null) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.ok(report);
    }

    @GetMapping
    public ResponseEntity<ReportResponse> getMyReport(@AuthenticationPrincipal Jwt jwt) {
        System.out.println(">>>Start getMyReport()");
        String userId = extractUserIdFromToken(jwt);
        System.out.println(">>UserId: " + userId);
        return getReport(userId, jwt);
    }

    private String extractUserIdFromToken(Jwt jwt) {
        // Извлекаем customer_id из JWT токена
        // Вариант 1: из subject
        String subject = jwt.getSubject();

        // Вариант 2: из custom claim
        Object customerIdClaim = jwt.getClaims().get("preferred_username");
        System.out.println(">> Attention: " + customerIdClaim.toString());

        if (customerIdClaim != null) {
            return customerIdClaim.toString();
        }

        // Если используем subject как ID
        return subject;
    }
}