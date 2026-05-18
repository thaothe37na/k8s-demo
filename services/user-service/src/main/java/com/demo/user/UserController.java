package com.demo.user;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/")
public class UserController {

    @GetMapping("/ping")
    public Map<String, String> ping() {
        Map<String, String> response = new HashMap<>();
        response.put("service", "user-service");
        response.put("status", "UP");
        response.put("message", "Pong from User Service!");
        return response;
    }

    @GetMapping("/info")
    public Map<String, Object> info() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "user-service");
        response.put("version", "1.0.0");
        return response;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "user-service");
        response.put("status", "UP");
        response.put("timestamp", Instant.now().toString());
        Runtime runtime = Runtime.getRuntime();
        response.put("memory_free_mb", runtime.freeMemory() / (1024 * 1024));
        response.put("memory_total_mb", runtime.totalMemory() / (1024 * 1024));
        return response;
    }
}
