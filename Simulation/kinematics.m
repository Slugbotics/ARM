close all; clear all;

L0 = 5.31;
L1 = 4.54;
L2 = 1.27;
L3 = 4.00;
L23 = L2 + L3;

P1 = [0 L0];

Q = [3,0,5];
T = [norm(Q(1:2)), Q(3)];

% calculate theta0 theta1 and theta2 here
theta2 = acos((norm(T-P1)^2 - L1^2 - L23^2)/(2*L1*L23));
mu = atan2(L23*sin(theta2), L1 + L23*cos(theta2));
TP1 = T - P1;
beta = atan2(TP1(1), -TP1(2));
theta1 = pi - mu - beta;
theta12 = theta1 + theta2;

% theta0 from 3d coords
theta0 = atan2(Q(2), Q(1));


P0 = [0 0];
P1 = [0 L0];
P2 = P1 + L1 * [sin(theta1) cos(theta1)];
P3 = P2 + L2 * [sin(theta12) cos(theta12)];
P4 = P3 + L3 * [sin(theta12) cos(theta12)];


% plot the range of the arm
R1 = L1 + L23;
R0 = abs(L1 - L23);
C0 = zeros(1000, 3);
C1 = zeros(1000, 3);

for i = 1:1000
    t = i * pi * 2 / 1000;
    C0(i,:) = R0 * [cos(t) sin(t) 0] + [0 0 L0];
    C1(i,:) = R1 * [cos(t) sin(t) 0] + [0 0 L0];
end

hold on
grid on

axis([-15 15 -15 15 -15 15]);


plot3(C0(:,1), C0(:,2), C0(:,3));
plot3(C1(:,1), C1(:,2), C1(:,3));


P = [P0; P1; P2; P3; P4];

S = [cos(theta0) * P(:,1) sin(theta0) * P(:,1) P(:,2)];

plot3(S(:,1), S(:,2), S(:,3))
plot3(Q(1), Q(2), Q(3), 'o')
xlim([-R1 R1]);
ylim([-R1 R1]);
zlim([0 L0 + R1]);

display(theta0 * 180 /pi)
display(theta1 * 180 /pi)
display(theta2 * 180 /pi)