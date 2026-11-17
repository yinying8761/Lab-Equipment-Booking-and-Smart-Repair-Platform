package com.labcare.service;

import com.labcare.common.BusinessException;
import com.labcare.domain.User;
import com.labcare.dto.AuthDtos;
import com.labcare.repository.UserRepository;
import com.labcare.security.CurrentUser;
import com.labcare.security.JwtUtil;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 登录与当前用户信息。
 */
@Service
public class AuthService {

    private final UserRepository userRepository;
    private final JwtUtil jwtUtil;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public AuthService(UserRepository userRepository, JwtUtil jwtUtil) {
        this.userRepository = userRepository;
        this.jwtUtil = jwtUtil;
    }

    @Transactional(readOnly = true)
    public AuthDtos.LoginResponse login(AuthDtos.LoginRequest request) {
        User user = userRepository.findByUsername(request.username().trim())
                .orElseThrow(() -> BusinessException.unauthorized("用户名或密码错误"));
        if (!encoder.matches(request.password(), user.getPasswordHash())) {
            throw BusinessException.unauthorized("用户名或密码错误");
        }
        if (user.getStatus() == null || user.getStatus() != 1) {
            throw BusinessException.forbidden("账号已停用，请联系管理员");
        }
        CurrentUser current = toCurrentUser(user);
        return new AuthDtos.LoginResponse(jwtUtil.issue(current), toView(user));
    }

    @Transactional(readOnly = true)
    public AuthDtos.UserView me(CurrentUser current) {
        User user = userRepository.findById(current.id())
                .orElseThrow(() -> BusinessException.unauthorized("账号不存在"));
        return toView(user);
    }

    public static CurrentUser toCurrentUser(User user) {
        return new CurrentUser(user.getId(), user.getUsername(), user.getDisplayName(), user.getRole().name());
    }

    public static AuthDtos.UserView toView(User user) {
        String roleLabel = user.getRole() == null ? "" : (user.getRole().name().equals("ADMIN") ? "管理员" : "普通用户");
        return new AuthDtos.UserView(user.getId(), user.getUsername(), user.getDisplayName(),
                user.getRole() == null ? "USER" : user.getRole().name(), roleLabel);
    }
}
