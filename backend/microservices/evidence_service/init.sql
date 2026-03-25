CREATE DATABASE IF NOT EXISTS evidence;
USE evidence;
 

CREATE TABLE IF NOT EXISTS evidence (
    evidenceID INT AUTO_INCREMENT PRIMARY KEY,
    disputeID INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    uploadedBy INT NOT NULL,
    fileURL VARCHAR(500) NOT NULL,
    fileType VARCHAR(50) NOT NULL,
    uploadedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    isApproved BOOLEAN DEFAULT FALSE,
    INDEX idx_disputeID (disputeID)
);
