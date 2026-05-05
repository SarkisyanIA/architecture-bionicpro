package com.example.reportservice.service;

import com.example.reportservice.model.ReportResponse;
import com.example.reportservice.repository.ClickHouseRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReportService {

    private final ClickHouseRepository clickHouseRepository;

    public ReportResponse getCustomerReport(String customerId) {
        log.info("Getting report for customer: {}", customerId);
        return clickHouseRepository.getCustomerReport(customerId);
    }
}