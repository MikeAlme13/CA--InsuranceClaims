// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract InsuranceClaims {
    enum ClaimStatus { Submitted, Approved, Rejected, Paid }

    struct Policy {
        address holder;
        uint256 premium;
        uint256 coverage;
        bool active;
    }

    struct Claim {
        uint256 id;
        address claimant;
        uint256 amount;
        bytes32 evidenceHash;
        ClaimStatus status;
    }

    address public insurer;
    mapping(address => Policy) public policies;
    Claim[] public claims;

    event PolicyCreated(address indexed holder, uint256 premium, uint256 coverage);
    event ClaimSubmitted(uint256 indexed id, address indexed claimant, uint256 amount);
    event ClaimDecided(uint256 indexed id, ClaimStatus status);
    event ClaimPaid(uint256 indexed id, address indexed to, uint256 amount);

    modifier onlyInsurer() {
        require(msg.sender == insurer, "Not insurer");
        _;
    }

    constructor() payable {
        insurer = msg.sender;
    }

    function createPolicy(address holder, uint256 premium, uint256 coverage) external onlyInsurer {
        policies[holder] = Policy(holder, premium, coverage, false);
        emit PolicyCreated(holder, premium, coverage);
    }

    function payPremium() external payable {
        Policy storage p = policies[msg.sender];
        require(p.holder == msg.sender, "Not policyholder");
        require(msg.value == p.premium, "Incorrect premium");
        p.active = true;
    }

    function submitClaim(uint256 amount, bytes32 evidenceHash) external {
        Policy storage p = policies[msg.sender];
        require(p.active, "Policy not active");
        require(amount <= p.coverage, "Amount exceeds coverage");

        uint256 id = claims.length;
        claims.push(Claim(id, msg.sender, amount, evidenceHash, ClaimStatus.Submitted));

        emit ClaimSubmitted(id, msg.sender, amount);
    }

    function approveClaim(uint256 id) external onlyInsurer {
        Claim storage c = claims[id];
        require(c.status == ClaimStatus.Submitted, "Not submitted");
        c.status = ClaimStatus.Approved;
        emit ClaimDecided(id, ClaimStatus.Approved);
    }

    function rejectClaim(uint256 id) external onlyInsurer {
        Claim storage c = claims[id];
        require(c.status == ClaimStatus.Submitted, "Not submitted");
        c.status = ClaimStatus.Rejected;
        emit ClaimDecided(id, ClaimStatus.Rejected);
    }

    function payClaim(uint256 id) external onlyInsurer {
        Claim storage c = claims[id];
        require(c.status == ClaimStatus.Approved, "Not approved");
        require(address(this).balance >= c.amount, "Insufficient funds");

        c.status = ClaimStatus.Paid;
        payable(c.claimant).transfer(c.amount);

        emit ClaimPaid(id, c.claimant, c.amount);
    }
}
